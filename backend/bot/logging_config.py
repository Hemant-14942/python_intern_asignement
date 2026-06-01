"""Structured logging helpers for request, response, and error audit trails."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class JsonFormatter(logging.Formatter):
    """Small JSON formatter that keeps log lines machine-readable."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key.startswith("_") or key in _STANDARD_LOG_FIELDS:
                continue
            payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str, separators=(",", ":"))


_STANDARD_LOG_FIELDS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
}


def configure_logging(log_file: str = "logs/trading_bot.log") -> None:
    """Configure root logging once for both CLI and FastAPI entry points."""

    root_logger = logging.getLogger()
    if getattr(root_logger, "_trading_bot_configured", False):
        return

    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    root_logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(JsonFormatter())
    file_handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    console_handler.setLevel(logging.WARNING)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    root_logger._trading_bot_configured = True  # type: ignore[attr-defined]
