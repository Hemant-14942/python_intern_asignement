"""Binance Futures Testnet client backed by the python-binance library."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from typing import Any

from binance.client import Client
from binance.exceptions import BinanceAPIException as PythonBinanceAPIException
from binance.exceptions import BinanceRequestException
from requests import RequestException

from backend.bot.config import Settings
from backend.bot.exceptions import BinanceAPIError, BinanceNetworkError, ConfigurationError

logger = logging.getLogger(__name__)


class BinanceFuturesClient:
    """Small wrapper around python-binance for Binance USDT-M Futures Testnet."""

    def __init__(
        self,
        settings: Settings,
        client_factory: Callable[..., Client] = Client,
    ) -> None:
        self.settings = settings
        self.base_url = settings.binance_base_url.rstrip("/")
        self._client_factory = client_factory

    async def ping(self) -> dict[str, str]:
        try:
            client = self._build_library_client(require_credentials=False)
            await asyncio.to_thread(client.futures_ping)
        except (BinanceRequestException, RequestException) as exc:
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

        try:
            client = self._build_library_client(require_credentials=True)
            response_payload = await asyncio.to_thread(client.futures_create_order, **payload)
        except PythonBinanceAPIException as exc:
            response_payload = {"code": exc.code, "msg": exc.message}
            logger.error(
                "binance_api_error",
                extra={
                    "event": "api_error",
                    "status_code": exc.status_code,
                    "payload": response_payload,
                    "request_payload": safe_payload,
                },
            )
            raise BinanceAPIError(exc.message, status_code=exc.status_code, payload=response_payload) from exc
        except (BinanceRequestException, RequestException) as exc:
            logger.exception("binance_network_error", extra={"event": "network_error", "payload": safe_payload})
            raise BinanceNetworkError(f"Network error while calling Binance: {exc}") from exc

        logger.info(
            "binance_order_response",
            extra={
                "event": "order_response",
                "payload": response_payload,
                "dry_run": False,
            },
        )

        return response_payload

    def _build_library_client(self, require_credentials: bool) -> Client:
        if require_credentials and (not self.settings.binance_api_key or not self.settings.binance_api_secret):
            logger.error("missing_binance_credentials", extra={"event": "configuration_error"})
            raise ConfigurationError("BINANCE_API_KEY and BINANCE_API_SECRET are required for live testnet orders.")

        client = self._client_factory(
            api_key=self.settings.binance_api_key,
            api_secret=self.settings.binance_api_secret,
            requests_params={"timeout": self.settings.request_timeout_seconds},
            testnet=True,
            ping=False,
        )
        client.FUTURES_TESTNET_URL = f"{self.base_url}/fapi"
        return client

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
