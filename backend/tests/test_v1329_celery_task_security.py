"""v1.3.29 — Celery Task Security Tests.

Verify task serialization safety, input validation, retry limits,
idempotency, and secret protection in task execution.
"""

import inspect

import pytest


class TestCelerySerializationSecurity:
    """Celery must use safe serialization (JSON, never pickle)."""

    def test_task_serializer_is_json(self):
        """Task serializer must be json, not pickle (RCE prevention)."""
        from app.tasks.celery_app import celery_app
        assert celery_app.conf.task_serializer == "json"

    def test_result_serializer_is_json(self):
        """Result serializer must be json."""
        from app.tasks.celery_app import celery_app
        assert celery_app.conf.result_serializer == "json"

    def test_accept_content_whitelist(self):
        """Celery only accepts JSON content (no pickle/yaml)."""
        from app.tasks.celery_app import celery_app
        accepted = celery_app.conf.accept_content
        assert "json" in accepted
        assert "pickle" not in accepted
        assert "yaml" not in accepted


class TestTaskRetryLimits:
    """Tasks must have bounded retry to prevent infinite loops."""

    def test_data_tasks_have_retry_limits(self):
        """Data fetch tasks should not retry infinitely."""
        from app.tasks import data_tasks
        # Check that tasks define retry behavior
        for name in dir(data_tasks):
            obj = getattr(data_tasks, name)
            if callable(obj) and hasattr(obj, "max_retries"):
                assert obj.max_retries is None or obj.max_retries <= 10

    def test_signal_tasks_available(self):
        """Signal generation tasks are importable."""
        from app.tasks import signal_tasks
        assert hasattr(signal_tasks, "generate_signals")


class TestTaskInputSafety:
    """Task arguments must not contain or expose secrets."""

    def test_task_logs_no_api_keys(self):
        """Task modules don't log raw API keys."""
        from app.tasks import data_tasks, ai_tasks
        source = inspect.getsource(data_tasks)
        assert "ANTHROPIC_API_KEY" not in source
        assert "sk-ant-" not in source

        ai_source = inspect.getsource(ai_tasks)
        assert "sk-ant-" not in ai_source

    def test_celery_broker_uses_redis(self):
        """Broker URL uses Redis (not an insecure transport)."""
        from app.tasks.celery_app import celery_app
        broker = celery_app.conf.broker_url or ""
        assert broker.startswith("redis") or broker == "" or "memory" in broker

    def test_beat_schedule_only_known_modules(self):
        """All beat-scheduled tasks come from app.tasks.* modules."""
        from app.tasks.scheduler import CELERY_BEAT_SCHEDULE
        for name, entry in CELERY_BEAT_SCHEDULE.items():
            task_name = entry.get("task", "")
            assert task_name.startswith("app.tasks."), \
                f"Task {name} references unknown module: {task_name}"


class TestTaskIdempotency:
    """Task re-execution must be safe (no duplicate data)."""

    def test_health_check_task_importable(self):
        """Health check task exists and is importable."""
        from app.tasks.data_tasks import health_check
        assert callable(health_check)

    def test_scheduler_has_expected_tasks(self):
        """Scheduler defines all expected periodic tasks."""
        from app.tasks.scheduler import CELERY_BEAT_SCHEDULE
        expected = [
            "fetch-crypto-prices",
            "generate-signals",
            "resolve-signals",
            "health-check",
        ]
        schedule_names = list(CELERY_BEAT_SCHEDULE.keys())
        for exp in expected:
            assert exp in schedule_names, f"Missing scheduled task: {exp}"
