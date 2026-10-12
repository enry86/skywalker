"""Star detection: whole-frame candidate search and sub-pixel centroiding in a tracking window."""

from __future__ import annotations

import cv2
import numpy as np

from skywalker.config import GuideConfig


def create_blob_detector(config: GuideConfig) -> cv2.SimpleBlobDetector:
    params = cv2.SimpleBlobDetector_Params()
    params.filterByArea = True
    params.minArea = config.min_area
    params.maxArea = config.max_area
    params.filterByCircularity = True
    params.minCircularity = config.min_circularity
    params.filterByConvexity = True
    params.minConvexity = config.min_convexity
    params.filterByInertia = True
    params.minInertiaRatio = config.min_inertia
    return cv2.SimpleBlobDetector_create(params)


def enhance_for_detection(gray: np.ndarray, use_clahe: bool) -> np.ndarray:
    """Contrast-stretch a frame for finding candidate stars and for display.

    The output distorts star brightness profiles, so it must not be used for centroiding.
    """
    if use_clahe:
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
    else:
        enhanced = cv2.equalizeHist(gray)
    return cv2.GaussianBlur(enhanced, (3, 3), 0)


def find_candidate_stars(
    enhanced: np.ndarray,
    detector: cv2.SimpleBlobDetector,
    min_area: float,
    max_area: float,
) -> list[tuple[float, float]]:
    """Return approximate star positions in the whole frame, largest first.

    Uses blob detection, falling back to thresholded contours when no blob passes the filters.
    """
    keypoints = list(detector.detect(enhanced))

    if not keypoints:
        _, thresh = cv2.threshold(enhanced, 200, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if min_area < area < max_area:
                m = cv2.moments(cnt)
                if m["m00"] != 0:
                    cx = m["m10"] / m["m00"]
                    cy = m["m01"] / m["m00"]
                    keypoints.append(cv2.KeyPoint(float(cx), float(cy), float(area**0.5)))

    keypoints.sort(key=lambda kp: kp.size, reverse=True)
    return [(kp.pt[0], kp.pt[1]) for kp in keypoints]


def nearest_star(
    stars: list[tuple[float, float]],
    point: tuple[float, float],
    max_distance: float,
) -> tuple[float, float] | None:
    """Return the star closest to ``point`` if it lies within ``max_distance`` pixels."""
    best: tuple[float, float] | None = None
    best_d2 = max_distance * max_distance
    for star in stars:
        d2 = (star[0] - point[0]) ** 2 + (star[1] - point[1]) ** 2
        if d2 <= best_d2:
            best, best_d2 = star, d2
    return best


def centroid_in_window(
    gray: np.ndarray,
    center: tuple[float, float],
    half_size: int,
    min_snr: float = 5.0,
    min_pixels: int = 3,
    iterations: int = 2,
) -> tuple[float, float] | None:
    """Measure the star near ``center`` with an intensity-weighted, background-subtracted centroid.

    Only the connected region around the brightest pixel in the window contributes, so a second
    star partially inside the window does not pull the result. The window is re-centred on the
    result and measured again to reduce bias when the star sits near the window edge.
    Returns ``None`` when no pixel rises ``min_snr`` noise levels above the background, or when
    the bright region has fewer than ``min_pixels`` pixels (noise spikes and hot pixels are
    single pixels, while a seeing-limited star spans several).
    """
    h, w = gray.shape[:2]
    cx, cy = center
    result: tuple[float, float] | None = None

    for _ in range(max(iterations, 1)):
        x0 = max(int(round(cx)) - half_size, 0)
        y0 = max(int(round(cy)) - half_size, 0)
        x1 = min(int(round(cx)) + half_size + 1, w)
        y1 = min(int(round(cy)) + half_size + 1, h)
        if x1 - x0 < 3 or y1 - y0 < 3:
            return None

        window = gray[y0:y1, x0:x1].astype(np.float32)
        background = float(np.median(window))
        # Half the 16-84 percentile spread is ~1 sigma for Gaussian noise; unlike the MAD it
        # does not collapse to whole numbers on 8-bit frames.
        p16, p84 = np.percentile(window, (16, 84))
        noise = max(float(p84 - p16) / 2.0, 1.0)
        signal = window - background

        peak_idx = np.unravel_index(int(np.argmax(signal)), signal.shape)
        peak = float(signal[peak_idx])
        if peak < min_snr * noise:
            return None

        threshold = max(3.0 * noise, 0.1 * peak)
        mask = (signal > threshold).astype(np.uint8)
        _, labels = cv2.connectedComponents(mask, connectivity=8)
        star_mask = labels == labels[peak_idx]
        if int(star_mask.sum()) < min_pixels:
            return None

        weights = np.where(star_mask, signal - threshold, 0.0)
        total = float(weights.sum())
        if total <= 0.0:
            return None

        ys, xs = np.indices(weights.shape, dtype=np.float32)
        cx = x0 + float((weights * xs).sum()) / total
        cy = y0 + float((weights * ys).sum()) / total
        result = (cx, cy)

    return result
