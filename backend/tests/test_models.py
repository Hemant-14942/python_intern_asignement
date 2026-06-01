from decimal import Decimal

import pytest
from pydantic import ValidationError

from backend.bot.models import OrderRequest, OrderSide, OrderType


def test_market_order_validation_normalizes_symbol() -> None:
    order = OrderRequest(symbol="btc/usdt", side=OrderSide.BUY, type=OrderType.MARKET, quantity=Decimal("0.001"))

    assert order.symbol == "BTCUSDT"
    assert order.order_type == OrderType.MARKET


def test_limit_order_requires_price() -> None:
    with pytest.raises(ValidationError, match="Price is required"):
        OrderRequest(symbol="BTCUSDT", side=OrderSide.SELL, type=OrderType.LIMIT, quantity=Decimal("0.001"))


def test_stop_limit_order_requires_stop_price() -> None:
    with pytest.raises(ValidationError, match="Stop price is required"):
        OrderRequest(
            symbol="ETHUSDT",
            side=OrderSide.BUY,
            type=OrderType.STOP_LIMIT,
            quantity=Decimal("0.01"),
            price=Decimal("3200"),
        )
