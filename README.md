# SkyWalker

SkyWalker is a small **autoguide prototype** for telescope setups: it captures video from a guide camera, finds candidate stars (blob detection with a contour fallback), lets you **lock** on a star with the mouse, then follows that star in a small tracking window with a sub-pixel centroid and shows the **pixel error** from the lock position. It uses **OpenCV** and is meant for experimentation until hardware drivers and guiding software are fully wired up.

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
| **Left-click** | Lock on the star nearest the click (green cross = its measured centroid; orange box = tracking window) |
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
| `-c N`, `--camera N` | `0` | OpenCV camera index |
| `--use-directshow` / `--no-use-directshow` | `True` | On Windows, prefer DirectShow (`CAP_DSHOW`; often needed for USB cameras). Linux always tries V4L2 first |
| `--no-directshow` | — | Short alias for `--no-use-directshow` |
| `--frame-width PX` | `640` | Requested frame width |
| `--frame-height PX` | `480` | Requested frame height |
| `--exposure VAL` | unset | Manual exposure; switches auto-exposure off. Units are backend-specific (see below) |
| `--gain VAL` | unset | `CAP_PROP_GAIN` (device-dependent) |
| `--fps FPS` | unset | Requested frame rate; lower rates allow longer exposures |

Unset camera options leave the driver's current setting alone. The values actually in effect are printed at startup.

**Exposure units:** V4L2 (Linux) uses driver units, often 100 µs steps; DirectShow (Windows) uses log2 seconds (e.g. `-5` = 1/32 s).
On Linux you can inspect and set controls directly, which also works when OpenCV cannot map a control:

```bash
v4l2-ctl -d /dev/video0 --list-ctrls
v4l2-ctl -d /dev/video0 -c <control>=<value>
```

### Star detection (blob filter)

| Option | Default | Description |
|--------|---------|-------------|
| `--min-area PX` | `5.0` | Minimum blob area |
| `--max-area PX` | `200.0` | Maximum blob area |
| `--min-circularity 0-1` | `0.6` | Minimum circularity |
| `--min-convexity 0-1` | `0.8` | Minimum convexity |
| `--min-inertia 0-1` | `0.5` | Minimum inertia ratio |
| `--clahe` / `--no-clahe` | `True` | Apply CLAHE before candidate detection (not used for centroiding) |

### Star tracking

| Option | Default | Description |
|--------|---------|-------------|
| `--track-half-size PX` | `15` | Half-width of the window that follows the locked star; nothing outside it is considered |
| `--snap-radius PX` | `25.0` | A click locks on the nearest detected star within this distance |

Inside the window the star position is a background-subtracted, intensity-weighted centroid of the connected region around the brightest pixel. Single-pixel spikes (hot pixels, noise) are rejected.

### RA motor control (phase 2)

| Option | Default | Description |
|--------|---------|-------------|
| `--serial-port PORT` | `""` | Arduino serial port (for example `/dev/ttyACM0` or `COM5`) |
| `--baud-rate N` | `115200` | Serial speed |
| `--serial-dry-run` / `--no-serial-dry-run` | `False` | Simulate serial link without hardware |
| `--sidereal-speed VAL` | `0.0` | Base open-loop RA speed setpoint |
| `--kp VAL` | `0.02` | Proportional gain from X drift to speed correction |
| `--deadband-px PX` | `0.8` | Ignore tiny X drift |
| `--max-correction VAL` | `0.5` | Clamp on correction term magnitude |
| `--command-hz HZ` | `8.0` | Command emission cadence |
| `--min-command-delta VAL` | `0.002` | Send early only if setpoint changed enough |
| `--keepalive SEC` | `2.0` | Resend the setpoint at least this often (keeps the firmware watchdog fed) |
| `--lock-loss-timeout SEC` | `1.0` | Time without the star before the status becomes `STAR_LOST` |

Without a lock, or while the star is lost, the motor keeps running at `--sidereal-speed`: stopping RA would carry the star out of the guide field within seconds. The motor is stopped only when the program exits (and by the firmware watchdog if the PC stops sending).

Omitted flags keep the defaults above. You can combine flags, for example:

```bash
python -m skywalker -c 0 --fps 5 --exposure 300 --gain 80
python -m skywalker --list-cameras
python -m skywalker --serial-dry-run --sidereal-speed 1.234 --kp 0.015
python -m skywalker --serial-port /dev/ttyACM0 --baud-rate 115200 --sidereal-speed 1.234
```

## Arduino serial protocol (phase 2 contract)

- `SET <speed_steps_per_s>\n` sets the absolute RA speed setpoint.
- `STOP\n` requests immediate motor stop.
- Use ASCII, newline-terminated lines.
- Recommended firmware behavior:
  - Parse `SET` and apply speed,
  - Optionally reply `ACK <speed>\n` for diagnostics,
  - Stop (or fall back to a safe speed) if no command is received before watchdog timeout.
- The host waits for `READY\n` after opening the port (opening it resets most boards), prints any
  non-`ACK` line it receives (e.g. `WATCHDOG STOP`), and resends `SET` at least every `--keepalive` seconds.

### Arduino sketch included

- A ready-to-adapt sketch is included at `skywalker_ra_controller/skywalker_ra_controller.ino`.
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
