"""Tests ensuring payment flow doesn't prematurely upgrade user tier.

B1 fix: The subscribe endpoint must NOT upgrade user tier immediately.
Tier upgrade should only happen via webhook after Razorpay confirms payment.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.mark.asyncio
async def test_create_subscription_sets_pending_status_for_paid():
    """create_subscription() should set 'pending' status for paid plans (monthly/annual).

    Paid subscriptions must NOT be active until Razorpay confirms payment.
    """
    from app.services.payment.razorpay_service import create_subscription

    mock_db = AsyncMock()
    mock_db.flush = AsyncMock()
    mock_db.add = MagicMock()

    sub = await create_subscription(mock_db, str(uuid.uuid4()), "monthly")
    assert sub.status == "pending"
    assert sub.plan == "monthly"

    sub_annual = await create_subscription(mock_db, str(uuid.uuid4()), "annual")
    assert sub_annual.status == "pending"
    assert sub_annual.plan == "annual"


@pytest.mark.asyncio
async def test_create_subscription_trial_is_active_immediately():
    """create_subscription() for trial plans should be 'active' immediately.

    Trials don't need payment confirmation.
    """
    from app.services.payment.razorpay_service import create_subscription

    mock_db = AsyncMock()
    mock_db.flush = AsyncMock()
    mock_db.add = MagicMock()

    sub = await create_subscription(mock_db, str(uuid.uuid4()), "trial")
    assert sub.status == "active"


@pytest.mark.asyncio
async def test_subscribe_endpoint_has_no_user_update():
    """Verify the create_paid_subscription handler source code has no User tier update.

    This is a structural test: the endpoint code must not contain imports
    or statements that upgrade the user tier.
    """
    import inspect

    from app.api.payments import create_paid_subscription

    source = inspect.getsource(create_paid_subscription)
    # Should NOT contain direct tier upgrade logic
    assert 'update(User)' not in source, \
        "create_paid_subscription should not update User tier — that belongs in webhook"
    assert 'tier="pro"' not in source, \
        "create_paid_subscription should not set tier to pro"


@pytest.mark.asyncio
async def test_webhook_handler_upgrades_user_tier():
    """handle_payment_success should update both subscription and user tier."""
    from app.services.payment.razorpay_service import handle_payment_success

    mock_db = AsyncMock()

    # Mock the subscription query to return a sub with a user_id
    mock_sub = MagicMock()
    mock_sub.user_id = str(uuid.uuid4())

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_sub
    # First call: update subscription, second call: select subscription, third call: update user
    mock_db.execute = AsyncMock(side_effect=[
        MagicMock(),      # UPDATE subscription
        mock_result,      # SELECT subscription
        MagicMock(),      # UPDATE user tier
    ])

    period_end = datetime.now(timezone.utc)
    await handle_payment_success(mock_db, "sub_razorpay_123", period_end)

    # Should have 3 execute calls: update sub, select sub, update user
    assert mock_db.execute.call_count == 3


@pytest.mark.asyncio
async def test_webhook_handler_handles_missing_subscription():
    """handle_payment_success should handle gracefully if subscription not found."""
    from app.services.payment.razorpay_service import handle_payment_success

    mock_db = AsyncMock()

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None  # No subscription found
    mock_db.execute = AsyncMock(side_effect=[
        MagicMock(),      # UPDATE subscription (no rows matched)
        mock_result,      # SELECT subscription returns None
    ])

    period_end = datetime.now(timezone.utc)
    # Should not raise — handles gracefully
    await handle_payment_success(mock_db, "sub_nonexistent_123", period_end)

    # Only 2 calls — no user update since sub not found
    assert mock_db.execute.call_count == 2
