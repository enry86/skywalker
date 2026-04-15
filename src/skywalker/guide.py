"""OpenCV-based guide camera loop: lock a star and report pixel error."""

from __future__ import annotations

import cv2

from skywalker.cameras import open_capture
from skywalker.config import GuideConfig

WINDOW_NAME = "Guide Camera - Star Tracker"


class GuideApp:
    """Capture frames, detect guide star, and show tracking error vs. a locked position."""

    def __init__(self, config: GuideConfig | None = None) -> None:
        self.config = config or GuideConfig()
        self.reference_pos: tuple[float, float] | None = None
        self.guide_star_pos: tuple[float, float] | None = None
        self.error_x: float = 0.0
        self.error_y: float = 0.0

        self._cap = open_capture(
            self.config.cam_index,
            use_directshow=self.config.use_directshow,
        )
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.frame_width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.frame_height)
        self._cap.set(cv2.CAP_PROP_EXPOSURE, self.config.exposure_value)
        self._cap.set(cv2.CAP_PROP_GAIN, self.config.gain_value)

        params = cv2.SimpleBlobDetector_Params()
        params.filterByArea = True
        params.minArea = self.config.min_area
        params.maxArea = self.config.max_area
        params.filterByCircularity = True
        params.minCircularity = self.config.min_circularity
        params.filterByConvexity = True
        params.minConvexity = self.config.min_convexity
        params.filterByInertia = True
        params.minInertiaRatio = self.config.min_inertia
        self._detector = cv2.SimpleBlobDetector_create(params)

        cv2.namedWindow(WINDOW_NAME)
        cv2.setMouseCallback(WINDOW_NAME, self._on_mouse)

    def _on_mouse(self, event: int, x: int, y: int, _flags: int, _param: object) -> None:
        if event == cv2.EVENT_LBUTTONDOWN:
            self.reference_pos = (float(x), float(y))
            print(f"Guide star locked at: {self.reference_pos}")

    def run(self) -> None:
        cfg = self.config
        print("Instructions:")
        print(" - Wait for stars to appear")
        print(" - Click on a bright, isolated star to lock it")
        print(" - Press 'r' to reset lock")
        print(" - Press 'q' to quit")

        try:
            while True:
                ret, frame = self._cap.read()
                if not ret:
                    print("Failed to grab frame")
                    break

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                if cfg.use_clahe:
                    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
                    gray = clahe.apply(gray)
                else:
                    gray = cv2.equalizeHist(gray)

                gray = cv2.GaussianBlur(gray, (3, 3), 0)

                keypoints = list(self._detector.detect(gray))

                if len(keypoints) == 0:
                    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
                    contours, _ = cv2.findContours(
                        thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
                    )
                    for cnt in contours:
                        area = cv2.contourArea(cnt)
                        if cfg.min_area < area < cfg.max_area:
                            m = cv2.moments(cnt)
                            if m["m00"] != 0:
                                cx = m["m10"] / m["m00"]
                                cy = m["m01"] / m["m00"]
                                size = float(area**0.5)
                                keypoints.append(cv2.KeyPoint(float(cx), float(cy), size))

                current_pos: tuple[float, float] | None = None
                if keypoints:
                    keypoints.sort(key=lambda kp: kp.size, reverse=True)
                    current_pos = (keypoints[0].pt[0], keypoints[0].pt[1])

                if self.reference_pos is not None and current_pos is not None:
                    self.error_x = current_pos[0] - self.reference_pos[0]
                    self.error_y = current_pos[1] - self.reference_pos[1]
                    self.guide_star_pos = current_pos
                else:
                    self.guide_star_pos = current_pos

                display = frame.copy()

                if self.reference_pos:
                    rx, ry = int(self.reference_pos[0]), int(self.reference_pos[1])
                    cv2.drawMarker(display, (rx, ry), (0, 255, 0), cv2.MARKER_CROSS, 20, 2)

                if self.guide_star_pos:
                    sx, sy = int(self.guide_star_pos[0]), int(self.guide_star_pos[1])
                    cv2.circle(display, (sx, sy), 12, (0, 0, 255), 2)

                info_text = f"Error X: {self.error_x:+.1f} px   Y: {self.error_y:+.1f} px"
                cv2.putText(
                    display,
                    info_text,
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 255, 0),
                    2,
                )

                if self.reference_pos:
                    cv2.putText(
                        display,
                        "LOCKED - Click again or 'r' to reset",
                        (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        2,
                    )
                else:
                    cv2.putText(
                        display,
                        "Click on a star to lock",
                        (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 0, 255),
                        2,
                    )

                cv2.imshow(WINDOW_NAME, display)

                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break
                if key == ord("r"):
                    self.reference_pos = None
                    print("Lock reset")
        finally:
            self._cap.release()
            cv2.destroyAllWindows()


def run_guide(config: GuideConfig | None = None) -> None:
    """Run the guide camera UI until the user quits."""
    GuideApp(config=config).run()
