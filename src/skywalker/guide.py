"""OpenCV-based guide camera loop: lock a star and report pixel error."""

from __future__ import annotations

import time

import cv2
import numpy as np

from skywalker.cameras import apply_capture_settings, open_capture
from skywalker.config import GuideConfig
from skywalker.control import GuidingSample, RAController, RAControllerConfig
from skywalker.detection import (
    centroid_in_window,
    create_blob_detector,
    enhance_for_detection,
    find_candidate_stars,
    nearest_star,
)
from skywalker.serial_link import SerialConfig, SerialSetpointLink

WINDOW_NAME = "Guide Camera - Star Tracker"


class GuideApp:
    """Capture frames, detect guide star, and show tracking error vs. a locked position."""

    def __init__(self, config: GuideConfig | None = None) -> None:
        self.config = config or GuideConfig()
        self.reference_pos: tuple[float, float] | None = None
        self.guide_star_pos: tuple[float, float] | None = None
        # Last measured position of the locked star; the tracking window is centred here.
        self.track_pos: tuple[float, float] | None = None
        self.error_x: float = 0.0
        self.error_y: float = 0.0
        self.last_sample: GuidingSample | None = None
        self.current_speed_cmd: float = self.config.sidereal_speed
        self.current_correction: float = 0.0
        self.filtered_error_x: float = 0.0
        self.tracking_status: str = "INIT"

        self._cap = open_capture(
            self.config.cam_index,
            use_directshow=self.config.use_directshow,
        )
        apply_capture_settings(
            self._cap,
            frame_width=self.config.frame_width,
            frame_height=self.config.frame_height,
            exposure=self.config.exposure_value,
            gain=self.config.gain_value,
            fps=self.config.fps,
        )
        self._detector = create_blob_detector(self.config)
        self._last_gray: np.ndarray | None = None
        self._last_candidates: list[tuple[float, float]] = []

        cv2.namedWindow(WINDOW_NAME)
        cv2.setMouseCallback(WINDOW_NAME, self._on_mouse)

    def _build_guiding_sample(
        self,
        current_pos: tuple[float, float] | None,
        now: float,
        dt_s: float,
    ) -> GuidingSample:
        locked = self.reference_pos is not None
        star_found = current_pos is not None
        return GuidingSample(
            timestamp_s=now,
            locked=locked,
            star_found=star_found,
            error_x=self.error_x,
            error_y=self.error_y,
            dt_s=dt_s,
        )

    def _on_mouse(self, event: int, x: int, y: int, _flags: int, _param: object) -> None:
        if event == cv2.EVENT_LBUTTONDOWN:
            self._lock_near((float(x), float(y)))

    def _lock_near(self, click: tuple[float, float]) -> None:
        """Lock on the star nearest the click, using its measured centroid as the reference."""
        if self._last_gray is None:
            return
        cfg = self.config
        seed = nearest_star(self._last_candidates, click, cfg.snap_radius_px) or click
        star = centroid_in_window(self._last_gray, seed, cfg.track_half_size)
        if star is None:
            print(f"No star found near {click}; lock not changed.")
            return
        self.reference_pos = star
        self.track_pos = star
        print(f"Guide star locked at: ({star[0]:.2f}, {star[1]:.2f})")

    def _reset_lock(self) -> None:
        self.reference_pos = None
        self.track_pos = None
        self.error_x = 0.0
        self.error_y = 0.0

    def run(self) -> None:
        cfg = self.config
        print("Instructions:")
        print(" - Wait for stars to appear")
        print(" - Click on a bright, isolated star to lock it")
        print(" - Press 'r' to reset lock")
        print(" - Press 'q' to quit")

        controller = RAController(
            RAControllerConfig(
                sidereal_speed=cfg.sidereal_speed,
                kp=cfg.kp,
                deadband_px=cfg.deadband_px,
                max_correction=cfg.max_correction,
                min_command_delta=cfg.min_command_delta,
                lock_loss_timeout_s=cfg.lock_loss_timeout_s,
                keepalive_s=cfg.keepalive_s,
            )
        )
        serial_link = SerialSetpointLink(
            SerialConfig(
                port=cfg.serial_port,
                baud_rate=cfg.baud_rate,
                dry_run=cfg.serial_dry_run,
                ready_timeout_s=cfg.serial_ready_timeout_s,
            )
        )
        command_period_s = 1.0 / max(cfg.command_hz, 0.1)
        next_command_ts = time.monotonic()
        prev_frame_ts = next_command_ts

        try:
            while True:
                now = time.monotonic()
                dt_s = max(now - prev_frame_ts, 1e-6)
                prev_frame_ts = now
                ret, frame = self._cap.read()
                if not ret:
                    print("Failed to grab frame")
                    break

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                enhanced = enhance_for_detection(gray, cfg.use_clahe)
                self._last_gray = gray
                self._last_candidates = find_candidate_stars(
                    enhanced, self._detector, cfg.min_area, cfg.max_area
                )

                current_pos: tuple[float, float] | None = None
                if self.reference_pos is not None and self.track_pos is not None:
                    # Follow the locked star only: other stars or hot pixels elsewhere in the
                    # frame must never be mistaken for it.
                    current_pos = centroid_in_window(gray, self.track_pos, cfg.track_half_size)
                    if current_pos is not None:
                        self.track_pos = current_pos
                        self.error_x = current_pos[0] - self.reference_pos[0]
                        self.error_y = current_pos[1] - self.reference_pos[1]
                    else:
                        self.error_x = 0.0
                        self.error_y = 0.0
                    self.guide_star_pos = current_pos
                else:
                    self.error_x = 0.0
                    self.error_y = 0.0
                    self.guide_star_pos = (
                        self._last_candidates[0] if self._last_candidates else None
                    )

                sample = self._build_guiding_sample(current_pos=current_pos, now=now, dt_s=dt_s)
                self.last_sample = sample

                if now >= next_command_ts:
                    next_command_ts = now + command_period_s
                    candidate = controller.compute(sample)
                    if controller.should_emit(
                        candidate, serial_link.last_sent, serial_link.seconds_since_send()
                    ):
                        serial_link.send_setpoint(candidate)
                    self.current_speed_cmd = candidate
                    self.current_correction = controller.last_correction
                    self.filtered_error_x = controller.filtered_error_x
                    self.tracking_status = controller.last_status

                for line in serial_link.poll_lines():
                    if not line.startswith("ACK"):
                        print(f"[arduino] {line}")

                display = frame.copy()

                if self.reference_pos:
                    rx, ry = int(self.reference_pos[0]), int(self.reference_pos[1])
                    cv2.drawMarker(display, (rx, ry), (0, 255, 0), cv2.MARKER_CROSS, 20, 2)
                if self.track_pos:
                    tx, ty = int(self.track_pos[0]), int(self.track_pos[1])
                    hs = cfg.track_half_size
                    cv2.rectangle(display, (tx - hs, ty - hs), (tx + hs, ty + hs), (0, 200, 255), 1)

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

                if self.reference_pos and self.guide_star_pos is None:
                    cv2.putText(
                        display,
                        "STAR LOST - holding base speed",
                        (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 0, 255),
                        2,
                    )
                elif self.reference_pos:
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

                port_text = "DRY-RUN" if cfg.serial_dry_run else cfg.serial_port or "N/A"
                control_text = (
                    f"Tracking: {self.tracking_status}   "
                    f"Port: {port_text}   CmdHz: {cfg.command_hz:.1f}"
                )
                cv2.putText(
                    display,
                    control_text,
                    (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (255, 200, 0),
                    2,
                )
                speed_text = (
                    f"Motor cmd: {self.current_speed_cmd:+.4f} stp/s   "
                    f"Base: {cfg.sidereal_speed:+.4f}   "
                    f"Corr: {self.current_correction:+.4f}"
                )
                cv2.putText(
                    display,
                    speed_text,
                    (10, 115),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (255, 200, 0),
                    2,
                )
                corr_text = (
                    f"Filt X: {self.filtered_error_x:+.2f} px   "
                    f"Kp: {cfg.kp:.4f}   Deadband: {cfg.deadband_px:.2f}px"
                )
                cv2.putText(
                    display,
                    corr_text,
                    (10, 140),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.55,
                    (255, 200, 0),
                    2,
                )

                cv2.imshow(WINDOW_NAME, display)

                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break
                if key == ord("r"):
                    self._reset_lock()
                    print("Lock reset")
        finally:
            try:
                serial_link.send_stop()
            finally:
                serial_link.close()
            self._cap.release()
            cv2.destroyAllWindows()


def run_guide(config: GuideConfig | None = None) -> None:
    """Run the guide camera UI until the user quits."""
    GuideApp(config=config).run()
