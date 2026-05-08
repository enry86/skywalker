# SkyWalker

SkyWalker is a small **autoguide prototype** for telescope setups: it captures video from a guide camera, detects a bright star (blob detection with a contour fallback), lets you **lock** a reference position with the mouse, and shows **pixel error** between the locked point and the tracked star. It uses **OpenCV** and is meant for experimentation until hardware drivers and guiding software are fully wired up.

Phase 2 adds RA motor driving over USB serial: Python computes a bounded speed command from star drift and streams setpoints to an Arduino controller.

**Requirements:** Python 3.11+, [OpenCV](https://opencv.org/) and NumPy (see `pyproject.toml`).

## Install

From the repository root:

```bash
pip install -e .
```

Developer tools (tests, Ruff):

```bash
pip install -e ".[dev]"
```

## Run

```bash
python -m skywalker
```

If the `skywalker` console script is on your `PATH` (after install):

```bash
skywalker
```

### Interactive window

| Action | Effect |
|--------|--------|
| **Left-click** | Lock guide position (green cross) on a star |
| **r** | Clear the lock |
| **q** | Quit |

## CLI reference

Global options (defaults match `GuideConfig` in `src/skywalker/config.py`):

| Option | Description |
|--------|-------------|
| `-h`, `--help` | Show help and exit |
| `--list-cameras` | Probe camera indices `0..9`, print which backends return a frame, then exit |

### Camera and capture

| Option | Default | Description |
|--------|---------|-------------|
| `-c N`, `--camera N` | `1` | OpenCV camera index |
| `--use-directshow` / `--no-use-directshow` | `True` | On Windows, prefer DirectShow (`CAP_DSHOW`; often needed for USB cameras) |
| `--no-directshow` | — | Short alias for `--no-use-directshow` |
| `--frame-width PX` | `640` | Requested frame width |
| `--frame-height PX` | `480` | Requested frame height |
| `--exposure VAL` | `-8.0` | `CAP_PROP_EXPOSURE` (device-dependent) |
| `--gain VAL` | `100.0` | `CAP_PROP_GAIN` (device-dependent) |

### Star detection (blob filter)

| Option | Default | Description |
|--------|---------|-------------|
| `--min-area PX` | `5.0` | Minimum blob area |
| `--max-area PX` | `200.0` | Maximum blob area |
| `--min-circularity 0-1` | `0.6` | Minimum circularity |
| `--min-convexity 0-1` | `0.8` | Minimum convexity |
| `--min-inertia 0-1` | `0.5` | Minimum inertia ratio |
| `--clahe` / `--no-clahe` | `True` | Apply CLAHE to the grayscale image before detection |

### RA motor control (phase 2)

| Option | Default | Description |
|--------|---------|-------------|
| `--serial-port PORT` | `""` | Arduino serial port (for example `COM5`) |
| `--baud-rate N` | `115200` | Serial speed |
| `--serial-dry-run` / `--no-serial-dry-run` | `False` | Simulate serial link without hardware |
| `--sidereal-speed VAL` | `0.0` | Base open-loop RA speed setpoint |
| `--kp VAL` | `0.02` | Proportional gain from X drift to speed correction |
| `--deadband-px PX` | `0.8` | Ignore tiny X drift |
| `--max-correction VAL` | `0.5` | Clamp on correction term magnitude |
| `--command-hz HZ` | `8.0` | Command emission cadence |
| `--min-command-delta VAL` | `0.002` | Send only if setpoint changed enough |
| `--lock-loss-timeout SEC` | `1.0` | Force stop when lock/star is stale |

Omitted flags keep the defaults above. You can combine flags, for example:

```bash
python -m skywalker -c 0 --exposure -10 --gain 80 --frame-width 800 --frame-height 600
python -m skywalker --list-cameras
python -m skywalker --serial-dry-run --sidereal-speed 1.234 --kp 0.015
python -m skywalker --serial-port COM5 --baud-rate 115200 --sidereal-speed 1.234
```

## Arduino serial protocol (phase 2 contract)

- `SET <speed_steps_per_s>\n` sets the absolute RA speed setpoint.
- `STOP\n` requests immediate motor stop.
- Use ASCII, newline-terminated lines.
- Recommended firmware behavior:
  - Parse `SET` and apply speed,
  - Optionally reply `ACK <speed>\n` for diagnostics,
  - Stop (or fall back to a safe speed) if no command is received before watchdog timeout.

### Arduino sketch included

- A ready-to-adapt sketch is included at `arduino/skywalker_ra_controller.ino`.
- The sketch now targets **Adafruit Motor Shield v1** via `AFMotor.h`.
- Install the Adafruit Motor Shield library so Arduino IDE can resolve `#include <AFMotor.h>`.
- It implements `SET`, `STOP`, `PING`, `STATUS`, plus watchdog stop.
- Update `MOTOR_CHANNEL` (M1..M4), `DIR_INVERTED`, and `SPEED_TO_PWM` for your hardware.
- Start with low values for `sidereal_speed`, `kp`, and `max_correction` while tuning.

### Isolated motor step test (no camera)

Use the helper script to send timed speed levels directly to Arduino:

```bash
python scripts/motor_step_test.py --port COM5 --baud 115200 --levels 0.2,0.5,1.0 --hold 2
```

Ramp test mode example:

```bash
python scripts/motor_step_test.py --port COM5 --mode ramp --ramp-min 0.1 --ramp-max 1.0 --ramp-step 0.05 --ramp-dt 0.2
```

Useful options:

- `--pause 0.5` pause at zero between levels
- `--bidirectional` also test negative levels (reverse direction)
- `--settle 2.0` wait after opening serial (Arduino auto-reset window)
- `--mode ramp` continuous up/down sweep instead of discrete steps
- `--ramp-min`, `--ramp-max`, `--ramp-step`, `--ramp-dt` ramp profile tuning

This script always sends `STOP` at start and end as a safety guard.

Windows launcher shortcuts (use project `venv` automatically):

- Step mode: `scripts\\run_motor_step.bat --port COM5 --levels 0.2,0.5,1.0 --hold 2`
- Ramp mode: `scripts\\run_motor_ramp.bat --port COM5 --ramp-min 0.1 --ramp-max 1.0 --ramp-step 0.05 --ramp-dt 0.2`

## License

MIT (see `pyproject.toml`).
