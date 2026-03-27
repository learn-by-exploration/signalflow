"""Shared async database engine for Celery tasks.

Provides a singleton engine that is reused across task invocations
instead of creating a new engine per task call. Includes proper
cleanup on worker shutdown.
"""

import threading

from celery.signals import worker_process_shutdown
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings

_engine = None
_session_factory = None
_lock = threading.Lock()


def get_task_engine():
    """Get or create the shared async engine for Celery tasks.

    Thread-safe with double-check locking pattern.
    """
    global _engine
    if _engine is None:
        with _lock:
            if _engine is None:
                settings = get_settings()
                _engine = create_async_engine(
                    settings.database_url,
                    pool_size=10,
                    max_overflow=5,
                    pool_pre_ping=True,
                    pool_recycle=1800,
                )
    return _engine


def get_task_session_factory():
    """Get or create the shared session factory for Celery tasks."""
    global _session_factory
    if _session_factory is None:
        with _lock:
            if _session_factory is None:
                _session_factory = async_sessionmaker(
                    get_task_engine(),
                    class_=AsyncSession,
                    expire_on_commit=False,
                )
    return _session_factory


@worker_process_shutdown.connect
def dispose_engine(**kwargs):
    """Clean up the shared engine when the Celery worker shuts down."""
    global _engine, _session_factory
    if _engine:
        import asyncio

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            loop.create_task(_engine.dispose())
        else:
            asyncio.run(_engine.dispose())
        _engine = None
        _session_factory = None
