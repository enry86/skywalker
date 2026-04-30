"""Serial transport for sending motor speed setpoints to Arduino."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SerialConfig:
    port: str
    baud_rate: int
    dry_run: bool = False
    timeout_s: float = 0.1


class SerialSetpointLink:
    """Best-effort line-based serial link for speed setpoints."""

    def __init__(self, config: SerialConfig) -> None:
        self._cfg = config
        self._serial = None
        self._last_sent: float | None = None

        if self._cfg.dry_run:
            return
        if not self._cfg.port:
            raise RuntimeError(
                "Serial port not configured. Use --serial-port COMx or --serial-dry-run."
            )
        self._serial = self._open_serial()

    @property
    def last_sent(self) -> float | None:
        return self._last_sent

    def send_setpoint(self, speed_steps_per_s: float) -> None:
        self._last_sent = speed_steps_per_s
        if self._cfg.dry_run:
            return
        line = f"SET {speed_steps_per_s:.6f}\n".encode("ascii")
        self._write(line)

    def send_stop(self) -> None:
        if self._cfg.dry_run:
            self._last_sent = 0.0
            return
        self._write(b"STOP\n")
        self._last_sent = 0.0

    def close(self) -> None:
        if self._cfg.dry_run:
            return
        if self._serial is not None:
            self._serial.close()
            self._serial = None

    def _open_serial(self):
        try:
            import serial  # type: ignore[import-not-found]
        except ImportError as exc:
            raise RuntimeError(
                "Missing dependency 'pyserial'. Install it to use USB serial control."
            ) from exc
        try:
            return serial.Serial(self._cfg.port, self._cfg.baud_rate, timeout=self._cfg.timeout_s)
        except Exception as exc:  # pragma: no cover - hardware-dependent path
            raise RuntimeError(
                f"Failed to open serial port {self._cfg.port!r} at {self._cfg.baud_rate} baud: {exc}"
            ) from exc

    def _write(self, payload: bytes) -> None:
        assert self._serial is not None
        try:
            self._serial.write(payload)
        except Exception:
            self._serial = self._open_serial()
            self._serial.write(payload)
