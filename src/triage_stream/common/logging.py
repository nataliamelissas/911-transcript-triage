"""Structured JSON logging so logs are queryable in prod (CloudWatch, etc.)."""
import logging
import sys

try:
    # canonical location since python-json-logger 3.0 (the old
    # `pythonjsonlogger.jsonlogger` path is deprecated)
    from pythonjsonlogger.json import JsonFormatter
except ImportError:  # keep import-safe before deps are installed
    JsonFormatter = None  # type: ignore[assignment, misc]


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    handler = logging.StreamHandler(sys.stdout)
    if JsonFormatter:
        handler.setFormatter(
            JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        )
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger
