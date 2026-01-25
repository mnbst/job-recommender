"""共通のログ設定とヘルパー."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

try:
    from google.cloud import logging as cloud_logging
except ModuleNotFoundError:
    cloud_logging = None


def is_cloud_run() -> bool:
    """Cloud Run環境のときにTrueを返す."""
    return bool(os.environ.get("K_SERVICE"))


def setup_logging() -> None:
    """ローカル/Cloud Run環境向けのログ設定."""
    if is_cloud_run():
        if cloud_logging is None:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )
            logging.getLogger(__name__).warning(
                "google.cloud.logging is not available; falling back to basic logging."
            )
            return

        client = cloud_logging.Client()
        client.setup_logging()
        return

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
