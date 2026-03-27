"""FinBERT vs Claude sentiment evaluation framework.

Provides tooling to compare FinBERT (free, deterministic, calibrated)
against Claude API for financial sentiment analysis.

This is an evaluation/comparison tool, not a production replacement.
Run via: python -m app.services.ai_engine.finbert_eval

Results are saved to finbert_eval_results.json for analysis.
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# FinBERT model identifier (HuggingFace)
FINBERT_MODEL = "ProsusAI/finbert"

# Evaluation metrics
EVAL_METRICS = [
    "correlation",  # Pearson correlation with Claude scores
    "cost_per_1k",  # USD cost per 1000 articles
    "latency_ms",  # Average latency in milliseconds
    "consistency",  # Score variance on same input (run 3x)
    "directional_accuracy",  # % agreement on bullish/bearish/neutral
]


def map_finbert_to_score(label: str, score: float) -> int:
    """Convert FinBERT label + confidence to 0-100 sentiment score.

    FinBERT outputs: positive, negative, neutral with confidence 0-1.

    Args:
        label: FinBERT label ('positive', 'negative', 'neutral').
        score: FinBERT confidence 0-1.

    Returns:
        Sentiment score 0-100 (same scale as Claude).
    """
    if label == "positive":
        return int(50 + score * 50)  # 50-100
    elif label == "negative":
        return int(50 - score * 50)  # 0-50
    else:  # neutral
        return int(50 + (score - 0.5) * 10)  # ~45-55


def compute_evaluation_metrics(
    claude_scores: list[int],
    finbert_scores: list[int],
    claude_latencies_ms: list[float] | None = None,
    finbert_latencies_ms: list[float] | None = None,
) -> dict[str, Any]:
    """Compute comparison metrics between Claude and FinBERT.

    Args:
        claude_scores: List of Claude sentiment scores (0-100).
        finbert_scores: List of FinBERT sentiment scores (0-100).
        claude_latencies_ms: Optional latency measurements for Claude.
        finbert_latencies_ms: Optional latency measurements for FinBERT.

    Returns:
        Dict with all evaluation metrics and a recommendation.
    """
    n = min(len(claude_scores), len(finbert_scores))
    if n == 0:
        return {"error": "No data to evaluate", "sample_size": 0}

    claude = claude_scores[:n]
    finbert = finbert_scores[:n]

    # Pearson correlation
    correlation = _pearson_correlation(claude, finbert)

    # Directional accuracy (agree on bullish/bearish/neutral)
    claude_dirs = [_to_direction(s) for s in claude]
    finbert_dirs = [_to_direction(s) for s in finbert]
    dir_agree = sum(1 for a, b in zip(claude_dirs, finbert_dirs) if a == b)
    directional_accuracy = dir_agree / n

    # Mean absolute error
    mae = sum(abs(a - b) for a, b in zip(claude, finbert)) / n

    # Cost comparison (Claude ~$0.003/article, FinBERT ~$0)
    claude_cost_per_1k = 3.00  # $3 per 1000 articles (API pricing)
    finbert_cost_per_1k = 0.00  # Free (local inference)

    # Latency comparison
    claude_avg_latency = (
        sum(claude_latencies_ms) / len(claude_latencies_ms)
        if claude_latencies_ms
        else 1500.0  # Estimate
    )
    finbert_avg_latency = (
        sum(finbert_latencies_ms) / len(finbert_latencies_ms)
        if finbert_latencies_ms
        else 50.0  # Estimate for local inference
    )

    # Decision recommendation
    recommendation = _generate_recommendation(correlation, directional_accuracy, n)

    return {
        "sample_size": n,
        "correlation": round(correlation, 4),
        "directional_accuracy": round(directional_accuracy, 4),
        "mean_absolute_error": round(mae, 2),
        "claude_cost_per_1k_usd": claude_cost_per_1k,
        "finbert_cost_per_1k_usd": finbert_cost_per_1k,
        "claude_avg_latency_ms": round(claude_avg_latency, 1),
        "finbert_avg_latency_ms": round(finbert_avg_latency, 1),
        "recommendation": recommendation,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
    }


def _pearson_correlation(x: list[int], y: list[int]) -> float:
    """Compute Pearson correlation coefficient."""
    n = len(x)
    if n < 2:
        return 0.0

    mean_x = sum(x) / n
    mean_y = sum(y) / n

    numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    denom_x = sum((xi - mean_x) ** 2 for xi in x) ** 0.5
    denom_y = sum((yi - mean_y) ** 2 for yi in y) ** 0.5

    if denom_x == 0 or denom_y == 0:
        return 0.0

    return numerator / (denom_x * denom_y)


def _to_direction(score: int) -> str:
    """Convert score to directional label."""
    if score >= 60:
        return "bullish"
    elif score <= 40:
        return "bearish"
    return "neutral"


def _generate_recommendation(
    correlation: float,
    directional_accuracy: float,
    sample_size: int,
) -> str:
    """Generate a recommendation based on evaluation results."""
    if sample_size < 50:
        return "INSUFFICIENT_DATA: Need at least 50 articles for reliable comparison."

    if correlation >= 0.9 and directional_accuracy >= 0.85:
        return "SWITCH_TO_FINBERT: High correlation and agreement. FinBERT saves ~$15/month with minimal quality loss."
    elif correlation >= 0.7 and directional_accuracy >= 0.75:
        return (
            "HYBRID: Use FinBERT for sentiment scoring, keep Claude for event chain reasoning only."
        )
    elif correlation >= 0.5:
        return "KEEP_CLAUDE: Moderate correlation. Claude provides meaningfully better analysis."
    else:
        return "KEEP_CLAUDE: Low correlation. Claude significantly outperforms FinBERT for this use case."


def save_evaluation_results(
    results: dict[str, Any],
    output_path: str = "finbert_eval_results.json",
) -> None:
    """Save evaluation results to JSON file.

    Args:
        results: Evaluation metrics dict.
        output_path: Output file path.
    """
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    logger.info("finbert_eval_saved", path=output_path)
