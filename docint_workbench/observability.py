from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from prometheus_client import CollectorRegistry, Counter, Histogram, generate_latest


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
        self._registry = CollectorRegistry(auto_describe=True)
        self._counters: dict[str, Counter] = {}
        self._counter_labels: dict[str, tuple[str, ...]] = {}
        self._histograms: dict[str, Histogram] = {}
        self._histogram_labels: dict[str, tuple[str, ...]] = {}

    def _counter(self, name: str, label_names: tuple[str, ...]) -> Counter:
        existing = self._counter_labels.get(name)
        if existing is None:
            self._counter_labels[name] = label_names
            self._counters[name] = Counter(name, name, labelnames=label_names, registry=self._registry)
        elif existing != label_names:
            raise ValueError(f"Counter '{name}' used with inconsistent labels: {existing} vs {label_names}")
        return self._counters[name]

    def _histogram(self, name: str, label_names: tuple[str, ...]) -> Histogram:
        existing = self._histogram_labels.get(name)
        if existing is None:
            self._histogram_labels[name] = label_names
            self._histograms[name] = Histogram(name, name, labelnames=label_names, registry=self._registry)
        elif existing != label_names:
            raise ValueError(
                f"Histogram '{name}' used with inconsistent labels: {existing} vs {label_names}"
            )
        return self._histograms[name]

    def inc(self, name: str, value: float = 1.0, **labels: str) -> None:
        label_names = tuple(sorted(labels.keys()))
        counter = self._counter(name, label_names)
        if label_names:
            counter.labels(**{key: labels[key] for key in label_names}).inc(value)
        else:
            counter.inc(value)

    def observe(self, name: str, value: float, **labels: str) -> None:
        label_names = tuple(sorted(labels.keys()))
        histogram = self._histogram(name, label_names)
        if label_names:
            histogram.labels(**{key: labels[key] for key in label_names}).observe(value)
        else:
            histogram.observe(value)

    def render_prometheus(self) -> str:
        return generate_latest(self._registry).decode("utf-8")


metrics = MetricsRegistry()
