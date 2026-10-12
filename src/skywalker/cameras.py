"""OpenCV capture helpers: per-OS backends, manual exposure, and camera probing."""

from __future__ import annotations

import sys

import cv2


def open_capture(
    index: int,
    *,
    use_directshow: bool = True,
) -> cv2.VideoCapture:
    """Open a camera by index, trying DirectShow (Windows) or V4L2 (Linux) first.

    Many USB guide cameras need ``CAP_DSHOW`` on Windows; the default MSMF backend
    often fails to open them even when the device is fine.
    """
    for _name, backend in _backends(use_directshow):
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
        "  • Linux: check `v4l2-ctl --list-devices` and that you are in the 'video' group.\n"
        "  • Device Manager: camera present without errors; install vendor drivers if needed.\n"
        "  • Windows: Settings → Privacy → Camera → allow desktop apps.\n"
        "  • Close other apps using the camera (Teams, browser, vendor software).\n"
        "  • Run: python -m skywalker --list-cameras"
    )


def _backends(use_directshow: bool) -> list[tuple[str, int | None]]:
    attempts: list[tuple[str, int | None]] = []
    if sys.platform == "win32" and use_directshow:
        attempts.append(("DirectShow", cv2.CAP_DSHOW))
    elif sys.platform.startswith("linux"):
        attempts.append(("V4L2", cv2.CAP_V4L2))
    attempts.append(("default", None))
    return attempts


def apply_capture_settings(
    cap: cv2.VideoCapture,
    *,
    frame_width: int,
    frame_height: int,
    exposure: float | None,
    gain: float | None,
    fps: float | None,
) -> None:
    """Configure the capture; ``None`` values leave the driver's current setting alone.

    Setting an exposure first switches auto-exposure off. The value that means "manual"
    differs per backend: V4L2 uses 1 (3 is aperture priority), DirectShow uses 0.25.
    Exposure units are backend-specific too (V4L2: driver units, often 100 µs;
    DirectShow: log2 seconds, e.g. -5 = 1/32 s).
    """
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
    if fps is not None:
        cap.set(cv2.CAP_PROP_FPS, fps)
    if exposure is not None:
        manual = 1 if cap.getBackendName() == "V4L2" else 0.25
        cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, manual)
        cap.set(cv2.CAP_PROP_EXPOSURE, exposure)
    if gain is not None:
        cap.set(cv2.CAP_PROP_GAIN, gain)

    print(
        f"Camera backend={cap.getBackendName()}  "
        f"size={cap.get(cv2.CAP_PROP_FRAME_WIDTH):.0f}x{cap.get(cv2.CAP_PROP_FRAME_HEIGHT):.0f}  "
        f"fps={cap.get(cv2.CAP_PROP_FPS):g}  exposure={cap.get(cv2.CAP_PROP_EXPOSURE):g}  "
        f"gain={cap.get(cv2.CAP_PROP_GAIN):g}"
    )


def probe_cameras(max_index: int = 10) -> None:
    """Print indices that successfully open and return at least one frame."""
    print(f"Probing camera indices 0..{max_index - 1} (this can take a few seconds)...\n")
    any_found = False
    for i in range(max_index):
        for label, backend in _backends(use_directshow=True):
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
        print("\nUse: python -m skywalker -c <index>")
