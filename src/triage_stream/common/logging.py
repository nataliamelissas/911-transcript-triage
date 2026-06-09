"""Structured JSON logging so logs are queryable in prod (CloudWatch, etc.)."""
import logging
import sys

try:
    from pythonjsonlogger import jsonlogger
except ImportError:  # keep import-safe before deps are installed
    jsonlogger = None


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    handler = logging.StreamHandler(sys.stdout)
    if jsonlogger:
        handler.setFormatter(
            jsonlogger.JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        )
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger
