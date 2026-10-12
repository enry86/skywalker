"""Serial transport for sending motor speed setpoints to Arduino."""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SerialConfig:
    port: str
    baud_rate: int
    dry_run: bool = False
    timeout_s: float = 0.1
    ready_timeout_s: float = 3.0


class SerialSetpointLink:
    """Best-effort line-based serial link for speed setpoints."""

    def __init__(self, config: SerialConfig) -> None:
        self._cfg = config
        self._serial = None
        self._last_sent: float | None = None
        self._last_send_ts: float | None = None
        self._rx_buffer = b""

        if self._cfg.dry_run:
            return
        if not self._cfg.port:
            raise RuntimeError(
                "Serial port not configured. Use --serial-port /dev/ttyACM0 or --serial-dry-run."
            )
        self._serial = self._open_serial()
        self._wait_ready()

    @property
    def last_sent(self) -> float | None:
        return self._last_sent

    def seconds_since_send(self) -> float:
        if self._last_send_ts is None:
            return float("inf")
        return time.monotonic() - self._last_send_ts

    def send_setpoint(self, speed_steps_per_s: float) -> None:
        self._mark_sent(speed_steps_per_s)
        if self._cfg.dry_run:
            return
        line = f"SET {speed_steps_per_s:.6f}\n".encode("ascii")
        self._write(line)

    def send_stop(self) -> None:
        if not self._cfg.dry_run:
            self._write(b"STOP\n")
        self._mark_sent(0.0)

    def poll_lines(self) -> list[str]:
        """Return complete lines received from the controller, without blocking."""
        if self._serial is None:
            return []
        try:
            waiting = self._serial.in_waiting
            if waiting:
                self._rx_buffer += self._serial.read(waiting)
        except Exception:
            return []
        *lines, self._rx_buffer = self._rx_buffer.split(b"\n")
        return [ln.decode("ascii", errors="replace").strip() for ln in lines if ln.strip()]

    def close(self) -> None:
        if self._cfg.dry_run:
            return
        if self._serial is not None:
            self._serial.close()
            self._serial = None

    def _mark_sent(self, value: float) -> None:
        self._last_sent = value
        self._last_send_ts = time.monotonic()

    def _wait_ready(self) -> None:
        """Wait for the sketch's READY banner; opening the port resets most Arduino boards."""
        deadline = time.monotonic() + self._cfg.ready_timeout_s
        while time.monotonic() < deadline:
            for line in self.poll_lines():
                if line == "READY":
                    return
            time.sleep(0.05)
        print(
            f"Warning: no READY from {self._cfg.port!r} within {self._cfg.ready_timeout_s:.1f}s; "
            "continuing anyway."
        )

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
                f"Failed to open serial port {self._cfg.port!r} "
                f"at {self._cfg.baud_rate} baud: {exc}"
            ) from exc

    def _write(self, payload: bytes) -> None:
        assert self._serial is not None
        try:
            self._serial.write(payload)
        except Exception:
            try:
                self._serial.close()
            except Exception:
                pass
            self._serial = self._open_serial()
            self._serial.write(payload)
