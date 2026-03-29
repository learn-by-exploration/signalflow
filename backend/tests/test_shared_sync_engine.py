"""Tests for shared sync engine — verifies connection pool leak fix (B2).

All data fetchers must use the same shared engine instance, NOT create
their own via create_engine().
"""

from unittest.mock import MagicMock, patch


def test_get_sync_engine_returns_singleton():
    """get_sync_engine() should return the same instance on repeated calls."""
    from app.services.data_ingestion import db as db_module

    # Reset the singleton
    db_module._sync_engine = None

    with patch.object(db_module, "create_engine") as mock_create:
        mock_engine = MagicMock()
        mock_create.return_value = mock_engine

        engine1 = db_module.get_sync_engine()
        engine2 = db_module.get_sync_engine()

        assert engine1 is engine2
        # create_engine should have been called exactly once
        mock_create.assert_called_once()

    # Cleanup
    db_module._sync_engine = None


def test_dispose_sync_engine():
    """dispose_sync_engine should reset the singleton."""
    from app.services.data_ingestion import db as db_module

    db_module._sync_engine = None

    with patch.object(db_module, "create_engine") as mock_create:
        mock_engine = MagicMock()
        mock_create.return_value = mock_engine

        db_module.get_sync_engine()
        assert db_module._sync_engine is not None

        db_module.dispose_sync_engine()
        assert db_module._sync_engine is None
        mock_engine.dispose.assert_called_once()

    db_module._sync_engine = None


def test_indian_stock_fetcher_uses_shared_engine():
    """IndianStockFetcher must use get_sync_engine(), not create_engine()."""
    import inspect

    from app.services.data_ingestion.indian_stocks import IndianStockFetcher

    source = inspect.getsource(IndianStockFetcher.__init__)
    assert "get_sync_engine()" in source
    assert "create_engine(" not in source


def test_crypto_fetcher_uses_shared_engine():
    """CryptoFetcher must use get_sync_engine(), not create_engine()."""
    import inspect

    from app.services.data_ingestion.crypto import CryptoFetcher

    source = inspect.getsource(CryptoFetcher.__init__)
    assert "get_sync_engine()" in source
    assert "create_engine(" not in source


def test_forex_fetcher_uses_shared_engine():
    """ForexFetcher must use get_sync_engine(), not create_engine()."""
    import inspect

    from app.services.data_ingestion.forex import ForexFetcher

    source = inspect.getsource(ForexFetcher.__init__)
    assert "get_sync_engine()" in source
    assert "create_engine(" not in source
