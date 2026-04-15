"""`python -m skywalker` entry point."""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace


def _build_parser(default) -> argparse.ArgumentParser:
    d = default
    p = argparse.ArgumentParser(
        prog="skywalker",
        description="Autoguide camera: lock a star and read pixel error.",
    )
    p.add_argument(
        "-c",
        "--camera",
        type=int,
        default=None,
        dest="cam_index",
        metavar="N",
        help=f"OpenCV camera index (default: {d.cam_index})",
    )
    p.add_argument(
        "--use-directshow",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=f"On Windows, prefer DirectShow (default: {d.use_directshow})",
    )
    p.add_argument(
        "--no-directshow",
        action="store_true",
        help="Same as --no-use-directshow (short alias).",
    )
    p.add_argument(
        "--frame-width",
        type=int,
        default=None,
        dest="frame_width",
        metavar="PX",
        help=f"Capture width (default: {d.frame_width})",
    )
    p.add_argument(
        "--frame-height",
        type=int,
        default=None,
        dest="frame_height",
        metavar="PX",
        help=f"Capture height (default: {d.frame_height})",
    )
    p.add_argument(
        "--exposure",
        type=float,
        default=None,
        dest="exposure_value",
        metavar="VAL",
        help=f"CAP_PROP_EXPOSURE (default: {d.exposure_value})",
    )
    p.add_argument(
        "--gain",
        type=float,
        default=None,
        dest="gain_value",
        metavar="VAL",
        help=f"CAP_PROP_GAIN (default: {d.gain_value})",
    )
    p.add_argument(
        "--min-area",
        type=float,
        default=None,
        dest="min_area",
        metavar="PX",
        help=f"Blob min area (default: {d.min_area})",
    )
    p.add_argument(
        "--max-area",
        type=float,
        default=None,
        dest="max_area",
        metavar="PX",
        help=f"Blob max area (default: {d.max_area})",
    )
    p.add_argument(
        "--min-circularity",
        type=float,
        default=None,
        dest="min_circularity",
        metavar="0-1",
        help=f"Blob min circularity (default: {d.min_circularity})",
    )
    p.add_argument(
        "--min-convexity",
        type=float,
        default=None,
        dest="min_convexity",
        metavar="0-1",
        help=f"Blob min convexity (default: {d.min_convexity})",
    )
    p.add_argument(
        "--min-inertia",
        type=float,
        default=None,
        dest="min_inertia",
        metavar="0-1",
        help=f"Blob min inertia ratio (default: {d.min_inertia})",
    )
    p.add_argument(
        "--clahe",
        dest="use_clahe",
        action=argparse.BooleanOptionalAction,
        default=None,
        help=f"Use CLAHE before detection (default: {d.use_clahe})",
    )
    p.add_argument(
        "--list-cameras",
        action="store_true",
        help="Probe indices and exit (which devices OpenCV can open).",
    )
    return p


def _config_from_args(args: argparse.Namespace, base):
    kw: dict = {}
    if args.cam_index is not None:
        kw["cam_index"] = args.cam_index
    if args.no_directshow:
        kw["use_directshow"] = False
    elif args.use_directshow is not None:
        kw["use_directshow"] = args.use_directshow
    if args.frame_width is not None:
        kw["frame_width"] = args.frame_width
    if args.frame_height is not None:
        kw["frame_height"] = args.frame_height
    if args.exposure_value is not None:
        kw["exposure_value"] = args.exposure_value
    if args.gain_value is not None:
        kw["gain_value"] = args.gain_value
    if args.min_area is not None:
        kw["min_area"] = args.min_area
    if args.max_area is not None:
        kw["max_area"] = args.max_area
    if args.min_circularity is not None:
        kw["min_circularity"] = args.min_circularity
    if args.min_convexity is not None:
        kw["min_convexity"] = args.min_convexity
    if args.min_inertia is not None:
        kw["min_inertia"] = args.min_inertia
    if args.use_clahe is not None:
        kw["use_clahe"] = args.use_clahe
    return replace(base, **kw) if kw else base


def main() -> int:
    from skywalker.config import GuideConfig

    base = GuideConfig()
    parser = _build_parser(base)
    args = parser.parse_args()

    if args.list_cameras:
        from skywalker.cameras import probe_cameras

        probe_cameras()
        return 0

    from skywalker.guide import run_guide

    try:
        run_guide(_config_from_args(args, base))
    except RuntimeError as e:
        print(e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
