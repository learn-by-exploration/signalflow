"""Historical calibration curve for confidence-to-win-rate mapping.

Uses resolved signal history to build a calibration curve that maps
confidence scores to actual win probabilities. This enables displaying
"Signals at 85% confidence historically hit target 72% of the time."

Uses isotonic regression for a smooth, monotonically increasing curve.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Minimum signals per bucket for reliable statistics
MIN_SIGNALS_PER_BUCKET = 10

# Confidence bins (edges)
CALIBRATION_BINS = [(0, 20), (20, 40), (40, 60), (60, 80), (80, 100)]


def compute_calibration_curve(
    resolved_signals: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compute calibration curve from resolved signal history.

    Args:
        resolved_signals: List of dicts with 'confidence' (int) and 'outcome' (str).
            Outcome must be one of: 'hit_target', 'hit_stop', 'expired'.

    Returns:
        Dict with:
            - bins: List of {range, count, wins, win_rate, is_reliable}
            - overall_win_rate: float
            - total_signals: int
            - calibration_error: float (mean absolute deviation from ideal)
            - is_calibrated: bool (True if enough data across bins)
    """
    if not resolved_signals:
        return _empty_calibration()

    # Bucket signals by confidence
    buckets: dict[tuple[int, int], list[dict]] = {b: [] for b in CALIBRATION_BINS}

    for sig in resolved_signals:
        confidence = sig.get("confidence", 0)
        outcome = sig.get("outcome", "")
        if outcome not in ("hit_target", "hit_stop"):
            continue  # Skip expired/pending — we only calibrate on resolved

        for low, high in CALIBRATION_BINS:
            if low <= confidence <= high:
                buckets[(low, high)].append(sig)
                break

    # Compute win rate per bucket
    bins_result = []
    all_wins = 0
    all_total = 0
    calibration_errors = []

    for low, high in CALIBRATION_BINS:
        signals_in_bin = buckets[(low, high)]
        count = len(signals_in_bin)
        wins = sum(1 for s in signals_in_bin if s["outcome"] == "hit_target")
        is_reliable = count >= MIN_SIGNALS_PER_BUCKET
        win_rate = wins / count if count > 0 else None

        # Expected win rate = midpoint of bin / 100 (ideal calibration)
        midpoint = (low + high) / 2 / 100
        if win_rate is not None:
            calibration_errors.append(abs(win_rate - midpoint))

        bins_result.append(
            {
                "range": f"{low}-{high}",
                "low": low,
                "high": high,
                "count": count,
                "wins": wins,
                "win_rate": round(win_rate, 4) if win_rate is not None else None,
                "is_reliable": is_reliable,
            }
        )

        all_wins += wins
        all_total += count

    overall_win_rate = all_wins / all_total if all_total > 0 else 0.0
    mean_cal_error = (
        sum(calibration_errors) / len(calibration_errors) if calibration_errors else 1.0
    )

    # Consider calibrated if at least 3 bins have reliable data
    reliable_bins = sum(1 for b in bins_result if b["is_reliable"])
    is_calibrated = reliable_bins >= 3

    return {
        "bins": bins_result,
        "overall_win_rate": round(overall_win_rate, 4),
        "total_signals": all_total,
        "calibration_error": round(mean_cal_error, 4),
        "is_calibrated": is_calibrated,
        "reliable_bins": reliable_bins,
    }


def apply_isotonic_smoothing(
    bins: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Apply isotonic regression to ensure win rates are monotonically increasing.

    This smooths out noise in small samples while maintaining
    the constraint that higher confidence should mean higher win rate.

    Args:
        bins: List of bin dicts from compute_calibration_curve.

    Returns:
        Updated bins with 'smoothed_win_rate' field added.
    """
    # Extract raw win rates (use midpoint for None)
    raw_rates = []
    for b in bins:
        if b["win_rate"] is not None:
            raw_rates.append(b["win_rate"])
        else:
            raw_rates.append(b["low"] / 100 + 0.1)  # Prior estimate

    # Pool Adjacent Violators (PAV) algorithm for isotonic regression
    smoothed = _pav_isotonic(raw_rates)

    result = []
    for b, sr in zip(bins, smoothed):
        b_copy = dict(b)
        b_copy["smoothed_win_rate"] = round(sr, 4)
        result.append(b_copy)

    return result


def _pav_isotonic(values: list[float]) -> list[float]:
    """Pool Adjacent Violators algorithm for isotonic regression.

    Ensures output is monotonically non-decreasing.
    """
    n = len(values)
    if n == 0:
        return []

    result = list(values)
    # Forward pass: fix violations
    changed = True
    while changed:
        changed = False
        i = 0
        while i < n - 1:
            if result[i] > result[i + 1]:
                # Pool: average the violating pair
                avg = (result[i] + result[i + 1]) / 2
                result[i] = avg
                result[i + 1] = avg
                changed = True
            i += 1

    return result


def get_predicted_win_rate(calibration: dict[str, Any], confidence: int) -> float | None:
    """Look up the predicted win rate for a given confidence score.

    Args:
        calibration: Result from compute_calibration_curve.
        confidence: Confidence score 0-100.

    Returns:
        Predicted win rate (0.0-1.0) or None if not calibrated.
    """
    if not calibration.get("is_calibrated"):
        return None

    bins = calibration.get("bins", [])
    for b in bins:
        if b["low"] <= confidence <= b["high"]:
            return b.get("smoothed_win_rate", b.get("win_rate"))

    return None


def _empty_calibration() -> dict[str, Any]:
    """Return empty calibration when no data is available."""
    return {
        "bins": [
            {
                "range": f"{low}-{high}",
                "low": low,
                "high": high,
                "count": 0,
                "wins": 0,
                "win_rate": None,
                "is_reliable": False,
            }
            for low, high in CALIBRATION_BINS
        ],
        "overall_win_rate": 0.0,
        "total_signals": 0,
        "calibration_error": 1.0,
        "is_calibrated": False,
        "reliable_bins": 0,
    }
