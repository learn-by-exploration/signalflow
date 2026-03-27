"""Prometheus metrics for SignalFlow monitoring.

Exposes key application metrics via /metrics endpoint for Grafana Cloud.
"""

import time
import logging
from collections import defaultdict
from typing import Any

logger = logging.getLogger(__name__)

# In-memory metrics store (lightweight, no external dependency needed)
# For production, swap with prometheus_client if available.

_counters: dict[str, int] = defaultdict(int)
_gauges: dict[str, float] = defaultdict(float)
_histograms: dict[str, list[float]] = defaultdict(list)

# Maximum histogram samples to retain (rolling window)
_MAX_HISTOGRAM_SAMPLES = 1000


def inc_counter(name: str, value: int = 1, labels: dict[str, str] | None = None) -> None:
    """Increment a counter metric."""
    key = _make_key(name, labels)
    _counters[key] += value


def set_gauge(name: str, value: float, labels: dict[str, str] | None = None) -> None:
    """Set a gauge metric."""
    key = _make_key(name, labels)
    _gauges[key] = value


def observe_histogram(name: str, value: float, labels: dict[str, str] | None = None) -> None:
    """Record a histogram observation."""
    key = _make_key(name, labels)
    samples = _histograms[key]
    samples.append(value)
    if len(samples) > _MAX_HISTOGRAM_SAMPLES:
        _histograms[key] = samples[-_MAX_HISTOGRAM_SAMPLES:]


def _make_key(name: str, labels: dict[str, str] | None = None) -> str:
    """Build metric key from name + sorted labels."""
    if not labels:
        return name
    label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
    return f"{name}{{{label_str}}}"


class Timer:
    """Context manager for timing operations.

    Usage:
        with Timer("api_request_duration", labels={"endpoint": "/signals"}):
            ...
    """

    def __init__(self, name: str, labels: dict[str, str] | None = None) -> None:
        self.name = name
        self.labels = labels
        self._start: float = 0.0

    def __enter__(self) -> "Timer":
        self._start = time.monotonic()
        return self

    def __exit__(self, *args: Any) -> None:
        duration = time.monotonic() - self._start
        observe_histogram(self.name, duration, self.labels)


def get_metrics_text() -> str:
    """Format all metrics in Prometheus exposition format.

    Returns:
        String in Prometheus text format.
    """
    lines: list[str] = []

    # Counters
    for key, value in sorted(_counters.items()):
        lines.append(f"# TYPE {_base_name(key)} counter")
        lines.append(f"{key} {value}")

    # Gauges
    for key, value in sorted(_gauges.items()):
        lines.append(f"# TYPE {_base_name(key)} gauge")
        lines.append(f"{key} {value}")

    # Histograms (emit count + sum + quantiles)
    seen_histograms: set[str] = set()
    for key, samples in sorted(_histograms.items()):
        base = _base_name(key)
        if base not in seen_histograms:
            seen_histograms.add(base)
            lines.append(f"# TYPE {base} summary")

        if samples:
            sorted_samples = sorted(samples)
            count = len(sorted_samples)
            total = sum(sorted_samples)
            p50 = sorted_samples[int(count * 0.5)] if count > 0 else 0
            p95 = sorted_samples[int(count * 0.95)] if count > 0 else 0
            p99 = sorted_samples[int(count * 0.99)] if count > 0 else 0

            labels_part = _extract_labels(key)
            q_prefix = _base_name(key)

            lines.append(f'{q_prefix}{{quantile="0.5"{_comma_labels(labels_part)}}} {p50:.6f}')
            lines.append(f'{q_prefix}{{quantile="0.95"{_comma_labels(labels_part)}}} {p95:.6f}')
            lines.append(f'{q_prefix}{{quantile="0.99"{_comma_labels(labels_part)}}} {p99:.6f}')
            lines.append(f"{key.replace('{', '_count{') if '{' in key else key + '_count'} {count}")
            lines.append(f"{key.replace('{', '_sum{') if '{' in key else key + '_sum'} {total:.6f}")

    return "\n".join(lines) + "\n" if lines else ""


def get_metrics_json() -> dict[str, Any]:
    """Return all metrics as a JSON-serializable dict."""
    return {
        "counters": dict(_counters),
        "gauges": dict(_gauges),
        "histograms": {
            k: {"count": len(v), "sum": sum(v), "p50": sorted(v)[len(v) // 2] if v else 0}
            for k, v in _histograms.items()
        },
    }


def _base_name(key: str) -> str:
    """Extract metric name without labels."""
    return key.split("{")[0] if "{" in key else key


def _extract_labels(key: str) -> str:
    """Extract labels portion from key."""
    if "{" in key and "}" in key:
        return key[key.index("{") + 1 : key.index("}")]
    return ""


def _comma_labels(labels: str) -> str:
    """Prepend comma if labels exist."""
    return f",{labels}" if labels else ""


# ── Pre-defined metric helpers ──


def record_signal_generated(market_type: str, signal_type: str) -> None:
    """Record a signal generation event."""
    inc_counter(
        "signalflow_signals_generated_total", labels={"market": market_type, "type": signal_type}
    )


def record_api_request(endpoint: str, method: str, status_code: int) -> None:
    """Record an API request."""
    inc_counter(
        "signalflow_api_requests_total",
        labels={"endpoint": endpoint, "method": method, "status": str(status_code)},
    )


def record_ai_api_call(task_type: str, tokens: int, cost_usd: float) -> None:
    """Record a Claude API call."""
    inc_counter("signalflow_ai_api_calls_total", labels={"task": task_type})
    inc_counter("signalflow_ai_tokens_total", value=tokens, labels={"task": task_type})
    _gauges["signalflow_ai_cost_usd_total"] = (
        _gauges.get("signalflow_ai_cost_usd_total", 0) + cost_usd
    )


def set_websocket_connections(count: int) -> None:
    """Update the active WebSocket connection gauge."""
    set_gauge("signalflow_websocket_connections_active", count)


def record_data_fetch(market_type: str, success: bool) -> None:
    """Record a data fetch attempt."""
    status = "success" if success else "error"
    inc_counter("signalflow_data_fetches_total", labels={"market": market_type, "status": status})
