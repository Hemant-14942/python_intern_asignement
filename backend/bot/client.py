"""Binance Futures Testnet REST client."""

from __future__ import annotations

import hashlib
import hmac
import logging
import time
from typing import Any
from urllib.parse import urlencode

import httpx

from backend.bot.config import Settings
from backend.bot.exceptions import BinanceAPIError, BinanceNetworkError, ConfigurationError

logger = logging.getLogger(__name__)


class BinanceFuturesClient:
    """Minimal signed REST client for Binance USDT-M Futures Testnet."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.base_url = settings.binance_base_url.rstrip("/")

    async def ping(self) -> dict[str, str]:
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.settings.request_timeout_seconds) as client:
                response = await client.get("/fapi/v1/ping")
                response.raise_for_status()
        except httpx.HTTPError as exc:
            logger.exception("binance_ping_failed")
            raise BinanceNetworkError(f"Unable to reach Binance Testnet: {exc}") from exc
        return {"status": "ok"}

    async def create_order(self, payload: dict[str, Any], dry_run: bool = False) -> dict[str, Any]:
        safe_payload = self._safe_payload(payload)
        logger.info("binance_order_request", extra={"event": "order_request", "payload": safe_payload, "dry_run": dry_run})

        if dry_run:
            response = self._dry_run_response(payload)
            logger.info("binance_order_response", extra={"event": "order_response", "payload": response, "dry_run": True})
            return response

        if not self.settings.binance_api_key or not self.settings.binance_api_secret:
            logger.error("missing_binance_credentials", extra={"event": "configuration_error"})
            raise ConfigurationError("BINANCE_API_KEY and BINANCE_API_SECRET are required for live testnet orders.")

        signed_payload = self._sign_payload(payload)
        headers = {"X-MBX-APIKEY": self.settings.binance_api_key}

        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self.settings.request_timeout_seconds) as client:
                response = await client.post("/fapi/v1/order", data=signed_payload, headers=headers)
        except httpx.HTTPError as exc:
            logger.exception("binance_network_error", extra={"event": "network_error", "payload": safe_payload})
            raise BinanceNetworkError(f"Network error while calling Binance: {exc}") from exc

        response_payload = self._parse_response(response)
        logger.info(
            "binance_order_response",
            extra={
                "event": "order_response",
                "status_code": response.status_code,
                "payload": response_payload,
                "dry_run": False,
            },
        )

        if response.is_error:
            message = response_payload.get("msg") or response.text
            raise BinanceAPIError(message, status_code=response.status_code, payload=response_payload)

        return response_payload

    def _sign_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        signed_payload = {**payload, "timestamp": int(time.time() * 1000), "recvWindow": 5000}
        query_string = urlencode(signed_payload)
        signature = hmac.new(
            self.settings.binance_api_secret.encode("utf-8"),  # type: ignore[union-attr]
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        signed_payload["signature"] = signature
        return signed_payload

    @staticmethod
    def _parse_response(response: httpx.Response) -> dict[str, Any]:
        try:
            return response.json()
        except ValueError:
            return {"raw": response.text}

    @staticmethod
    def _safe_payload(payload: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in payload.items() if key not in {"signature"}}

    @staticmethod
    def _dry_run_response(payload: dict[str, Any]) -> dict[str, Any]:
        now = int(time.time() * 1000)
        return {
            "orderId": f"dry-run-{now}",
            "symbol": payload["symbol"],
            "status": "DRY_RUN_ACCEPTED",
            "clientOrderId": f"dryrun-{now}",
            "price": payload.get("price", "0"),
            "avgPrice": "0",
            "origQty": payload["quantity"],
            "executedQty": "0",
            "cumQuote": "0",
            "timeInForce": payload.get("timeInForce", "GTC"),
            "type": payload["type"],
            "side": payload["side"],
            "stopPrice": payload.get("stopPrice", "0"),
            "updateTime": now,
        }
