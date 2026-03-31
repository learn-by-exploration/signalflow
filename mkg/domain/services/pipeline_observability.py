# mkg/domain/services/pipeline_observability.py
"""PipelineObservability — metrics, health checks, and timing for the MKG pipeline.

R-OB1 through R-OB5: Records stage timing, throughput counters, error rates,
and provides health status and Prometheus-compatible metric export.
"""

import time
from contextlib import contextmanager
from typing import Any, Generator


class PipelineObservability:
    """Observability layer for the MKG processing pipeline.

    Tracks stage durations, throughput counters, and error rates.
    Provides health check and Prometheus text export.
    """

    def __init__(self, error_threshold: int = 5) -> None:
        self._stages: dict[str, list[float]] = {}
        self._counters: dict[str, int] = {}
        self._errors: dict[str, int] = {}
        self._error_threshold = error_threshold

    def record_stage(self, stage: str, duration_ms: float) -> None:
        """Record a stage execution time.

        Args:
            stage: Stage name (ingestion, extraction, propagation, etc.).
            duration_ms: Duration in milliseconds.
        """
        self._stages.setdefault(stage, []).append(duration_ms)

    def increment(self, counter: str, value: int = 1) -> None:
        """Increment a throughput counter.

        Args:
            counter: Counter name.
            value: Amount to increment by.
        """
        self._counters[counter] = self._counters.get(counter, 0) + value

    def record_error(self, stage: str, error_type: str) -> None:
        """Record an error occurrence.

        Args:
            stage: Stage where the error occurred.
            error_type: Error class name.
        """
        self._errors[stage] = self._errors.get(stage, 0) + 1

    @contextmanager
    def timer(self, stage: str) -> Generator[None, None, None]:
        """Context manager that times a stage and records it.

        Usage:
            with observer.timer("extraction"):
                do_extraction()
        """
        start = time.monotonic()
        try:
            yield
        finally:
            elapsed_ms = (time.monotonic() - start) * 1000
            self.record_stage(stage, elapsed_ms)

    def get_metrics(self) -> dict[str, Any]:
        """Get all recorded metrics.

        Returns:
            Dict with stages, counters, and errors sections.
        """
        stages: dict[str, dict[str, Any]] = {}
        for name, timings in self._stages.items():
            stages[name] = {
                "count": len(timings),
                "avg_ms": sum(timings) / len(timings) if timings else 0,
                "min_ms": min(timings) if timings else 0,
                "max_ms": max(timings) if timings else 0,
            }

        return {
            "stages": stages,
            "counters": dict(self._counters),
            "errors": dict(self._errors),
        }

    def health_check(self) -> dict[str, Any]:
        """Check pipeline health based on error rates.

        Returns:
            Dict with status (healthy, degraded, unhealthy) and details.
        """
        total_errors = sum(self._errors.values())

        if total_errors >= self._error_threshold * 2:
            status = "unhealthy"
        elif total_errors >= self._error_threshold:
            status = "degraded"
        else:
            status = "healthy"

        return {
            "status": status,
            "total_errors": total_errors,
            "stages_tracked": len(self._stages),
            "counters": dict(self._counters),
        }

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus text format.

        Returns:
            Prometheus-compatible metrics string.
        """
        lines: list[str] = []

        for name, timings in self._stages.items():
            count = len(timings)
            avg = sum(timings) / count if count else 0
            lines.append(f"mkg_stage_{name}_count {count}")
            lines.append(f"mkg_stage_{name}_avg_ms {avg:.2f}")

        for name, value in self._counters.items():
            lines.append(f"mkg_{name} {value}")

        for name, count in self._errors.items():
            lines.append(f"mkg_errors_{name} {count}")

        return "\n".join(lines)

    def reset(self) -> None:
        """Reset all metrics."""
        self._stages.clear()
        self._counters.clear()
        self._errors.clear()
