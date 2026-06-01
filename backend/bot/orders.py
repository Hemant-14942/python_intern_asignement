"""Order placement orchestration."""

from __future__ import annotations

from decimal import Decimal

from backend.bot.client import BinanceFuturesClient
from backend.bot.models import OrderRequest, OrderResponse, OrderType
from backend.bot.validators import decimal_to_binance


class TradingBot:
    """High-level order service shared by CLI and API."""

    def __init__(self, client: BinanceFuturesClient) -> None:
        self.client = client

    async def place_order(self, order: OrderRequest) -> OrderResponse:
        payload = self._build_binance_payload(order)
        raw_response = await self.client.create_order(payload, dry_run=order.dry_run)
        return self._normalize_response(order, raw_response)

    @staticmethod
    def _build_binance_payload(order: OrderRequest) -> dict[str, str]:
        payload = {
            "symbol": order.symbol,
            "side": order.side.value,
            "type": _map_order_type(order.order_type),
            "quantity": decimal_to_binance(order.quantity),
            "newOrderRespType": "RESULT",
        }

        if order.order_type in {OrderType.LIMIT, OrderType.STOP_LIMIT}:
            payload["timeInForce"] = "GTC"
            payload["price"] = decimal_to_binance(order.price)  # type: ignore[arg-type]

        if order.order_type == OrderType.STOP_LIMIT:
            payload["stopPrice"] = decimal_to_binance(order.stop_price)  # type: ignore[arg-type]
            payload["workingType"] = "CONTRACT_PRICE"

        return payload

    @staticmethod
    def _normalize_response(order: OrderRequest, raw_response: dict) -> OrderResponse:
        return OrderResponse(
            symbol=raw_response.get("symbol", order.symbol),
            side=order.side,
            order_type=order.order_type,
            order_id=raw_response.get("orderId", "unknown"),
            status=raw_response.get("status", "UNKNOWN"),
            executed_qty=_decimal_or_zero(raw_response.get("executedQty")),
            avg_price=_decimal_or_none(raw_response.get("avgPrice") or raw_response.get("price")),
            dry_run=order.dry_run,
            raw=raw_response,
        )


def _map_order_type(order_type: OrderType) -> str:
    if order_type == OrderType.STOP_LIMIT:
        return "STOP"
    return order_type.value


def _decimal_or_zero(value: object) -> Decimal:
    if value in (None, ""):
        return Decimal("0")
    return Decimal(str(value))


def _decimal_or_none(value: object) -> Decimal | None:
    if value in (None, "", "0"):
        return None
    return Decimal(str(value))
