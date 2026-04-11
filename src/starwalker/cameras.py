"""OpenCV capture helpers: Windows DirectShow and camera probing."""

from __future__ import annotations

import sys

import cv2


def open_capture(
    index: int,
    *,
    use_directshow: bool = True,
) -> cv2.VideoCapture:
    """Open a camera by index, trying DirectShow on Windows first when enabled.

    Many USB guide cameras need ``CAP_DSHOW`` on Windows; the default MSMF backend
    often fails to open them even when the device is fine.
    """
    attempts: list[tuple[str, int | None]] = []
    if sys.platform == "win32" and use_directshow:
        attempts.append(("DirectShow", cv2.CAP_DSHOW))
    attempts.append(("default", None))

    for _name, backend in attempts:
        cap = cv2.VideoCapture(index, backend) if backend is not None else cv2.VideoCapture(index)
        if not cap.isOpened():
            cap.release()
            continue
        ok, frame = cap.read()
        if ok and frame is not None:
            return cap
        cap.release()

    raise RuntimeError(
        f"Camera index {index} did not open or return a frame.\n"
        "  • Re-seat the USB cable; try another port (USB 2 vs 3).\n"
        "  • Device Manager: camera present without errors; install vendor drivers if needed.\n"
        "  • Windows: Settings → Privacy → Camera → allow desktop apps.\n"
        "  • Close other apps using the camera (Teams, browser, vendor software).\n"
        "  • Run: python -m starwalker --list-cameras"
    )


def probe_cameras(max_index: int = 10) -> None:
    """Print indices that successfully open and return at least one frame."""
    print(f"Probing camera indices 0..{max_index - 1} (this can take a few seconds)...\n")
    any_found = False
    for i in range(max_index):
        if sys.platform == "win32":
            pairs = (("DirectShow", cv2.CAP_DSHOW), ("default", None))
        else:
            pairs = (("default", None),)
        for label, backend in pairs:
            cap = cv2.VideoCapture(i, backend) if backend is not None else cv2.VideoCapture(i)
            if not cap.isOpened():
                cap.release()
                continue
            ok, frame = cap.read()
            cap.release()
            if ok and frame is not None:
                h, w = frame.shape[:2]
                print(f"  OK  index={i}  backend={label}  frame {w}x{h}")
                any_found = True
                break

    if not any_found:
        print("  No cameras responded. If the device is plugged in, check drivers and privacy.")
    else:
        print("\nUse: python -m starwalker -c <index>")
