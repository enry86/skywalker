"""Timed serial motor test for Arduino RA control.

Example:
    python scripts/motor_step_test.py --port COM5 --baud 115200 --levels 0.2,0.5,1.0 --hold 2
"""

from __future__ import annotations

import argparse
import time

try:
    import serial  # type: ignore[import-not-found]
except ImportError as exc:  # pragma: no cover - environment dependent
    raise SystemExit("Missing dependency 'pyserial'. Install with: pip install pyserial") from exc


def parse_levels(raw: str) -> list[float]:
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    if not parts:
        raise argparse.ArgumentTypeError("Provide at least one level, e.g. 0.2,0.5,1.0")
    try:
        return [float(p) for p in parts]
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Invalid level list {raw!r}") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run isolated motor speed test over serial (SET/STOP protocol)."
    )
    parser.add_argument("--port", required=True, help="Serial port (e.g. COM5)")
    parser.add_argument("--baud", type=int, default=115200, help="Serial baud rate")
    parser.add_argument(
        "--mode",
        choices=["step", "ramp"],
        default="step",
        help="Test mode: step levels or continuous ramp (default: step)",
    )
    parser.add_argument(
        "--levels",
        type=parse_levels,
        default=[0.2, 0.5, 1.0],
        help="Comma-separated speed levels for step mode, e.g. 0.2,0.5,1.0",
    )
    parser.add_argument("--hold", type=float, default=2.0, help="Seconds to hold each level")
    parser.add_argument(
        "--pause", type=float, default=0.5, help="Seconds to pause at zero between levels"
    )
    parser.add_argument(
        "--bidirectional",
        action="store_true",
        help="Also run the negative levels after positive ones",
    )
    parser.add_argument(
        "--settle",
        type=float,
        default=2.0,
        help="Initial wait after opening serial (seconds)",
    )
    parser.add_argument(
        "--ramp-min",
        type=float,
        default=0.0,
        help="Ramp mode minimum speed magnitude (default: 0.0)",
    )
    parser.add_argument(
        "--ramp-max",
        type=float,
        default=1.0,
        help="Ramp mode maximum speed magnitude (default: 1.0)",
    )
    parser.add_argument(
        "--ramp-step",
        type=float,
        default=0.05,
        help="Ramp mode increment per update (default: 0.05)",
    )
    parser.add_argument(
        "--ramp-dt",
        type=float,
        default=0.2,
        help="Ramp mode update period in seconds (default: 0.2)",
    )
    return parser


def write_line(ser: serial.Serial, line: str) -> None:
    ser.write((line + "\n").encode("ascii"))
    print(f"> {line}")


def _run_step_mode(ser: serial.Serial, args: argparse.Namespace) -> None:
    levels: list[float] = list(args.levels)
    if args.bidirectional:
        levels = levels + [-x for x in levels]

    for idx, level in enumerate(levels, start=1):
        print(f"[{idx}/{len(levels)}] Hold speed {level:+.4f} for {args.hold:.2f}s")
        write_line(ser, f"SET {level:.6f}")
        time.sleep(args.hold)

        print(f"  Pause at zero for {args.pause:.2f}s")
        write_line(ser, "SET 0.000000")
        time.sleep(args.pause)


def _frange(start: float, stop: float, step: float) -> list[float]:
    values: list[float] = []
    value = start
    while value < stop:
        values.append(value)
        value += step
    values.append(stop)
    return values


def _run_ramp_mode(ser: serial.Serial, args: argparse.Namespace) -> None:
    ramp_min = abs(args.ramp_min)
    ramp_max = abs(args.ramp_max)
    ramp_step = abs(args.ramp_step)
    if ramp_step == 0.0:
        raise SystemExit("--ramp-step must be > 0")
    if ramp_max < ramp_min:
        raise SystemExit("--ramp-max must be >= --ramp-min")

    up = _frange(ramp_min, ramp_max, ramp_step)
    down = list(reversed(up[:-1]))
    sequence = up + down
    if args.bidirectional:
        neg = [-x for x in sequence]
        sequence = sequence + [0.0] + neg

    print(
        "Ramp sequence: "
        f"{len(sequence)} points, min={ramp_min:.4f}, max={ramp_max:.4f}, step={ramp_step:.4f}, dt={args.ramp_dt:.3f}s"
    )
    for idx, level in enumerate(sequence, start=1):
        print(f"[{idx}/{len(sequence)}] Ramp speed {level:+.4f}")
        write_line(ser, f"SET {level:.6f}")
        time.sleep(args.ramp_dt)


def run_test(args: argparse.Namespace) -> None:
    with serial.Serial(args.port, args.baud, timeout=0.2) as ser:
        print(f"Opened {args.port} @ {args.baud}")
        print(f"Waiting {args.settle:.1f}s for board reset...")
        time.sleep(args.settle)

        write_line(ser, "STOP")
        time.sleep(0.2)

        try:
            if args.mode == "step":
                _run_step_mode(ser, args)
            else:
                _run_ramp_mode(ser, args)
        finally:
            print("Stopping motor...")
            write_line(ser, "STOP")
            time.sleep(0.2)

    print("Motor test complete.")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    run_test(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
