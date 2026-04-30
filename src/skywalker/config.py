"""Default camera and star-detection settings for autoguiding."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GuideConfig:
    """Tunable parameters for the guide camera and blob-based star detection."""

    cam_index: int = 1
    use_directshow: bool = True
    frame_width: int = 640
    frame_height: int = 480
    exposure_value: float = -8.0
    gain_value: float = 100.0

    min_area: float = 5.0
    max_area: float = 200.0
    min_circularity: float = 0.6
    min_convexity: float = 0.8
    min_inertia: float = 0.5

    use_clahe: bool = True

    serial_port: str = ""
    baud_rate: int = 115200
    sidereal_speed: float = 0.0
    kp: float = 0.02
    deadband_px: float = 0.8
    max_correction: float = 0.5
    command_hz: float = 8.0
    min_command_delta: float = 0.002
    lock_loss_timeout_s: float = 1.0
    serial_dry_run: bool = False
