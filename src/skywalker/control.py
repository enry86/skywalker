"""RA-axis control logic for hybrid open/closed-loop guiding."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GuidingSample:
    """Single guiding measurement exposed by the tracking loop."""

    timestamp_s: float
    locked: bool
    star_found: bool
    error_x: float
    error_y: float
    dt_s: float


@dataclass(frozen=True, slots=True)
class RAControllerConfig:
    """Tunable limits and gains for RA speed control."""

    sidereal_speed: float
    kp: float
    deadband_px: float
    max_correction: float
    min_command_delta: float
    lock_loss_timeout_s: float
    alpha: float = 0.2


class RAController:
    """Hybrid controller: open-loop sidereal with bounded drift correction."""

    def __init__(self, config: RAControllerConfig) -> None:
        self._cfg = config
        self._filtered_error_x = 0.0
        self._last_command = config.sidereal_speed
        self._last_valid_sample_ts = 0.0

    @property
    def last_command(self) -> float:
        return self._last_command

    def compute(self, sample: GuidingSample) -> float:
        if sample.locked and sample.star_found:
            self._last_valid_sample_ts = sample.timestamp_s
            self._filtered_error_x = self._low_pass(sample.error_x)
            correction = self._correction_from_error(self._filtered_error_x)
            command = self._cfg.sidereal_speed + correction
        else:
            stale = (sample.timestamp_s - self._last_valid_sample_ts) > self._cfg.lock_loss_timeout_s
            command = self._cfg.sidereal_speed if not stale else 0.0

        self._last_command = command
        return command

    def should_emit(self, candidate: float, last_sent: float | None) -> bool:
        if last_sent is None:
            return True
        return abs(candidate - last_sent) >= self._cfg.min_command_delta

    def _low_pass(self, value: float) -> float:
        alpha = self._cfg.alpha
        return (1.0 - alpha) * self._filtered_error_x + alpha * value

    def _correction_from_error(self, error_x: float) -> float:
        if abs(error_x) <= self._cfg.deadband_px:
            return 0.0
        correction = self._cfg.kp * error_x
        limit = self._cfg.max_correction
        return max(-limit, min(limit, correction))
