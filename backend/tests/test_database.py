"""Tests for database setup and dependency injection."""

import pytest

from app.database import Base, get_db


class TestBase:
    def test_base_is_declarative(self):
        """Base class is a DeclarativeBase."""
        assert hasattr(Base, "metadata")
        assert hasattr(Base, "registry")


class TestGetDb:
    @pytest.mark.asyncio
    async def test_get_db_is_async_generator(self):
        """get_db should be an async generator."""
        import inspect
        assert inspect.isasyncgenfunction(get_db)
