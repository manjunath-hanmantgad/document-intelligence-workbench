from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, timezone


LOGGER_NAME = "docint_workbench"


def _utc_now() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": _utc_now(),
            "level": record.levelname.lower(),
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "event"):
            payload["event"] = getattr(record, "event")
        if hasattr(record, "fields"):
            payload["fields"] = getattr(record, "fields")
        return json.dumps(payload, separators=(",", ":"))


def configure_logging(level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger(LOGGER_NAME)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        logger.propagate = False
    logger.setLevel(level.upper())
    return logger


def log_event(logger: logging.Logger, level: str, event: str, **fields: object) -> None:
    logger.log(getattr(logging, level.upper(), logging.INFO), event, extra={"event": event, "fields": fields})


class MetricsRegistry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: dict[tuple[str, tuple[tuple[str, str], ...]], float] = {}
        self._histograms: dict[tuple[str, tuple[tuple[str, str], ...]], list[float]] = {}

    def inc(self, name: str, value: float = 1.0, **labels: str) -> None:
        key = (name, tuple(sorted(labels.items())))
        with self._lock:
            self._counters[key] = self._counters.get(key, 0.0) + value

    def observe(self, name: str, value: float, **labels: str) -> None:
        key = (name, tuple(sorted(labels.items())))
        with self._lock:
            bucket = self._histograms.setdefault(key, [])
            bucket.append(value)

    def render_prometheus(self) -> str:
        lines: list[str] = []
        with self._lock:
            for (name, labels), value in sorted(self._counters.items(), key=lambda item: item[0][0]):
                lines.append(f"{name}{_fmt_labels(labels)} {value}")
            for (name, labels), values in sorted(self._histograms.items(), key=lambda item: item[0][0]):
                if not values:
                    continue
                count = len(values)
                total = sum(values)
                minimum = min(values)
                maximum = max(values)
                lines.append(f"{name}_count{_fmt_labels(labels)} {count}")
                lines.append(f"{name}_sum{_fmt_labels(labels)} {total}")
                lines.append(f"{name}_min{_fmt_labels(labels)} {minimum}")
                lines.append(f"{name}_max{_fmt_labels(labels)} {maximum}")
        return "\n".join(lines) + ("\n" if lines else "")


def _fmt_labels(labels: tuple[tuple[str, str], ...]) -> str:
    if not labels:
        return ""
    parts = [f'{key}="{value}"' for key, value in labels]
    return "{" + ",".join(parts) + "}"


metrics = MetricsRegistry()
