"""Default camera and star-detection settings for autoguiding."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GuideConfig:
    """Tunable parameters for the guide camera and blob-based star detection."""

    cam_index: int = 0
    use_directshow: bool = True
    frame_width: int = 640
    frame_height: int = 480
    # None leaves the driver's current setting untouched (see README for per-OS units).
    exposure_value: float | None = None
    gain_value: float | None = None
    fps: float | None = None

    min_area: float = 5.0
    max_area: float = 200.0
    min_circularity: float = 0.6
    min_convexity: float = 0.8
    min_inertia: float = 0.5

    use_clahe: bool = True

    track_half_size: int = 15
    snap_radius_px: float = 25.0

    serial_port: str = ""
    baud_rate: int = 115200
    serial_dry_run: bool = False
    serial_ready_timeout_s: float = 3.0
    sidereal_speed: float = 0.0
    kp: float = 0.02
    deadband_px: float = 0.8
    max_correction: float = 0.5
    command_hz: float = 8.0
    min_command_delta: float = 0.002
    keepalive_s: float = 2.0
    lock_loss_timeout_s: float = 1.0
