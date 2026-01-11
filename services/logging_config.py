"""共通のログ設定とヘルパー."""

from __future__ import annotations

import json
import logging
import os
from typing import Any


def is_cloud_run() -> bool:
    """Cloud Run環境のときにTrueを返す."""
    return bool(os.environ.get("K_SERVICE"))


def setup_logging() -> None:
    """ローカル/Cloud Run環境向けのログ設定."""
    if is_cloud_run():
        import google.cloud.logging

        client = google.cloud.logging.Client()
        client.setup_logging()
    else:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )


def log_structured(
    logger: logging.Logger,
    message: str,
    *,
    level: int = logging.INFO,
    exc_info: bool | BaseException | None = None,
    **fields: Any,
) -> None:
    """Cloud Runでは構造化ログ、ローカルでは可読なテキストで出力."""
    if is_cloud_run():
        extra = {"json_fields": fields} if fields else None
        logger.log(level, message, extra=extra, exc_info=exc_info)
        return

    if fields:
        message = f"{message}: {json.dumps(fields, ensure_ascii=False)}"
    logger.log(level, message, exc_info=exc_info)
