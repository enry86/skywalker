"""Tests for star detection and centroiding on synthetic frames."""

import numpy as np

from skywalker.detection import centroid_in_window, nearest_star


def _frame(
    stars: list[tuple[float, float, float]],
    shape: tuple[int, int] = (120, 160),
    background: float = 20.0,
    noise: float = 2.0,
    sigma: float = 1.5,
    seed: int = 0,
) -> np.ndarray:
    """8-bit frame with Gaussian stars given as (x, y, peak) on a noisy background."""
    rng = np.random.default_rng(seed)
    ys, xs = np.indices(shape, dtype=np.float64)
    img = np.full(shape, background) + rng.normal(0.0, noise, shape)
    for x, y, peak in stars:
        img += peak * np.exp(-((xs - x) ** 2 + (ys - y) ** 2) / (2 * sigma**2))
    return np.clip(img, 0, 255).astype(np.uint8)


def test_centroid_is_subpixel_accurate() -> None:
    gray = _frame([(60.3, 50.7, 150.0)])
    pos = centroid_in_window(gray, (62.0, 49.0), half_size=10)
    assert pos is not None
    assert abs(pos[0] - 60.3) < 0.15
    assert abs(pos[1] - 50.7) < 0.15


def test_centroid_ignores_brighter_star_outside_window() -> None:
    gray = _frame([(40.0, 40.0, 80.0), (120.0, 80.0, 230.0)])
    pos = centroid_in_window(gray, (41.0, 41.0), half_size=10)
    assert pos is not None
    assert abs(pos[0] - 40.0) < 0.2
    assert abs(pos[1] - 40.0) < 0.2


def test_centroid_not_pulled_by_neighbour_inside_window() -> None:
    gray = _frame([(50.0, 50.0, 150.0), (60.0, 50.0, 100.0)])
    pos = centroid_in_window(gray, (50.0, 50.0), half_size=12)
    assert pos is not None
    assert abs(pos[0] - 50.0) < 0.3


def test_centroid_none_on_empty_sky() -> None:
    gray = _frame([])
    assert centroid_in_window(gray, (80.0, 60.0), half_size=10) is None


def test_centroid_near_frame_edge() -> None:
    gray = _frame([(3.0, 4.0, 150.0)])
    pos = centroid_in_window(gray, (2.0, 2.0), half_size=10)
    assert pos is not None
    assert abs(pos[0] - 3.0) < 0.3
    assert abs(pos[1] - 4.0) < 0.3


def test_nearest_star_respects_radius() -> None:
    stars = [(10.0, 10.0), (50.0, 50.0)]
    assert nearest_star(stars, (45.0, 52.0), max_distance=10.0) == (50.0, 50.0)
    assert nearest_star(stars, (100.0, 100.0), max_distance=10.0) is None


def test_centroid_rejects_hot_pixel() -> None:
    gray = _frame([])
    gray[60, 80] = 255
    assert centroid_in_window(gray, (80.0, 60.0), half_size=10) is None


def test_centroid_rejects_noise_over_many_frames() -> None:
    for seed in range(200):
        assert centroid_in_window(_frame([], seed=seed), (80.0, 60.0), half_size=15) is None
