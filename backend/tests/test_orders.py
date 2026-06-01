from decimal import Decimal

import pytest

from backend.bot.client import BinanceFuturesClient
from backend.bot.config import Settings
from backend.bot.models import OrderRequest, OrderSide, OrderType
from backend.bot.orders import TradingBot


@pytest.mark.asyncio
async def test_dry_run_market_order_response() -> None:
    bot = TradingBot(BinanceFuturesClient(Settings()))
    order = OrderRequest(
        symbol="BTCUSDT",
        side=OrderSide.BUY,
        type=OrderType.MARKET,
        quantity=Decimal("0.001"),
        dry_run=True,
    )

    response = await bot.place_order(order)

    assert str(response.order_id).startswith("dry-run-")
    assert response.status == "DRY_RUN_ACCEPTED"
    assert response.executed_qty == Decimal("0")
    assert response.dry_run is True


def test_stop_limit_maps_to_binance_stop_payload() -> None:
    order = OrderRequest(
        symbol="ETHUSDT",
        side=OrderSide.SELL,
        type=OrderType.STOP_LIMIT,
        quantity=Decimal("0.02"),
        price=Decimal("3100"),
        stop_price=Decimal("3150"),
    )

    payload = TradingBot._build_binance_payload(order)

    assert payload["type"] == "STOP"
    assert payload["timeInForce"] == "GTC"
    assert payload["price"] == "3100"
    assert payload["stopPrice"] == "3150"
