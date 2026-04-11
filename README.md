# StarWalker

StarWalker is a small **autoguide prototype** for telescope setups: it captures video from a guide camera, detects a bright star (blob detection with a contour fallback), lets you **lock** a reference position with the mouse, and shows **pixel error** between the locked point and the tracked star. It uses **OpenCV** and is meant for experimentation until hardware drivers and guiding software are fully wired up.

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
python -m starwalker
```

If the `starwalker` console script is on your `PATH` (after install):

```bash
starwalker
```

### Interactive window

| Action | Effect |
|--------|--------|
| **Left-click** | Lock guide position (green cross) on a star |
| **r** | Clear the lock |
| **q** | Quit |

## CLI reference

Global options (defaults match `GuideConfig` in `src/starwalker/config.py`):

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

Omitted flags keep the defaults above. You can combine flags, for example:

```bash
python -m starwalker -c 0 --exposure -10 --gain 80 --frame-width 800 --frame-height 600
python -m starwalker --list-cameras
```

## License

MIT (see `pyproject.toml`).
