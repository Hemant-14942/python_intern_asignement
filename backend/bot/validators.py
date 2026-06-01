"""Reusable validation and normalization helpers."""

from __future__ import annotations

from decimal import Decimal

from backend.bot.models import OrderRequest, OrderSide, OrderType


def decimal_to_binance(value: Decimal) -> str:
    """Return a non-scientific decimal string accepted by Binance."""

    normalized = value.normalize()
    return format(normalized, "f")


def build_order_request(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str | Decimal,
    price: str | Decimal | None = None,
    stop_price: str | Decimal | None = None,
    dry_run: bool = False,
) -> OrderRequest:
    """Create a validated order request from raw CLI/API values."""

    return OrderRequest(
        symbol=symbol,
        side=OrderSide(side.upper()),
        type=OrderType(order_type.upper()),
        quantity=Decimal(str(quantity)),
        price=Decimal(str(price)) if price not in (None, "") else None,
        stop_price=Decimal(str(stop_price)) if stop_price not in (None, "") else None,
        dry_run=dry_run,
    )
