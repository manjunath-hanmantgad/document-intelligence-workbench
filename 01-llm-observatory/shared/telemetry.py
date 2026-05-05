import logging
from typing import Any

from shared.config import get_settings


def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


def track_event(name: str, properties: dict[str, Any] | None = None) -> None:
    settings = get_settings()
    logger = setup_logger("telemetry")
    properties = properties or {}

    if settings.applicationinsights_connection_string:
        logger.info("cloud_event=%s properties=%s", name, properties)
    else:
        logger.info("local_event=%s properties=%s", name, properties)
