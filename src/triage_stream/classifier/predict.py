"""Inference wrapper around the registered model, with timeout + fallback.

TODO(you):
  1. Load the model from the MLflow registry at startup (not per-request).
  2. classify(text) -> Classification with score, keywords, model_version, latency.
  3. Enforce settings.infer_timeout_ms; on timeout/error, FALL BACK to a cheap
     keyword rule so the system degrades gracefully instead of dropping the call.
"""
from __future__ import annotations

from triage_stream.common.schemas import Classification


class UrgencyClassifier:
    def __init__(self) -> None:
        self._model = None
        self._version = "uninitialized"

    def classify(self, call_id: str, seq: int, text: str) -> Classification:
        raise NotImplementedError("Day 3: implement inference + timeout fallback")
