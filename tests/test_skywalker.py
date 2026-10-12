"""Tests for the skywalker package."""

from skywalker import __version__
from skywalker.control import GuidingSample, RAController, RAControllerConfig


def test_version() -> None:
    assert __version__ == "0.1.0"


def _controller() -> RAController:
    return RAController(
        RAControllerConfig(
            sidereal_speed=1.0,
            kp=0.1,
            deadband_px=1.0,
            max_correction=0.2,
            min_command_delta=0.01,
            lock_loss_timeout_s=0.5,
            alpha=1.0,
        )
    )


def test_deadband_keeps_sidereal_speed() -> None:
    ctl = _controller()
    sample = GuidingSample(1.0, locked=True, star_found=True, error_x=0.5, error_y=0.0, dt_s=0.1)
    assert ctl.compute(sample) == 1.0


def test_correction_is_clamped() -> None:
    ctl = _controller()
    sample = GuidingSample(1.0, locked=True, star_found=True, error_x=50.0, error_y=0.0, dt_s=0.1)
    assert ctl.compute(sample) == 1.2


def test_lock_loss_keeps_sidereal_speed() -> None:
    ctl = _controller()
    valid = GuidingSample(1.0, locked=True, star_found=True, error_x=2.0, error_y=0.0, dt_s=0.1)
    ctl.compute(valid)

    transient_loss = GuidingSample(
        1.3, locked=False, star_found=False, error_x=0.0, error_y=0.0, dt_s=0.1
    )
    assert ctl.compute(transient_loss) == 1.0

    stale_loss = GuidingSample(
        1.7, locked=True, star_found=False, error_x=0.0, error_y=0.0, dt_s=0.1
    )
    assert ctl.compute(stale_loss) == 1.0
    assert ctl.last_status == "STAR_LOST"


def test_waiting_for_lock_tracks_at_sidereal() -> None:
    ctl = _controller()
    sample = GuidingSample(100.0, locked=False, star_found=True, error_x=0.0, error_y=0.0, dt_s=0.1)
    assert ctl.compute(sample) == 1.0
    assert ctl.last_status == "WAIT_LOCK"


def test_emit_threshold() -> None:
    ctl = _controller()
    assert ctl.should_emit(1.0, None)
    assert not ctl.should_emit(1.005, 1.0)
    assert ctl.should_emit(1.02, 1.0)


def test_emit_keepalive_resends_unchanged_setpoint() -> None:
    ctl = _controller()
    assert not ctl.should_emit(1.0, 1.0, since_last_send_s=1.9)
    assert ctl.should_emit(1.0, 1.0, since_last_send_s=2.0)


def test_config_from_args_maps_only_given_options() -> None:
    from skywalker.__main__ import _build_parser, _config_from_args
    from skywalker.config import GuideConfig

    base = GuideConfig()
    args = _build_parser(base).parse_args(["--kp", "0.04", "--no-directshow", "--fps", "5"])
    cfg = _config_from_args(args, base)
    assert cfg.kp == 0.04
    assert cfg.fps == 5.0
    assert cfg.use_directshow is False
    assert cfg.sidereal_speed == base.sidereal_speed
