"""FastAPI serving layer. Async, Pydantic-validated, observable.

Provided: app + health/readiness probes (prod basics).
TODO(you):
  - POST /classify : text -> Classification (wire UrgencyClassifier).
  - POST /route    : Classification -> RouteDecision (wire router.decide).
  - WS  /stream    : accept AudioChunks -> ASR -> classify -> route (the e2e path).
  - Add Prometheus metrics + request latency histogram.
"""
from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(title="triage-stream", version="0.1.0")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """Liveness: process is up."""
    return {"status": "ok"}


@app.get("/readyz")
def readyz() -> dict[str, str]:
    """Readiness: model loaded & deps reachable. TODO: real checks."""
    return {"status": "ready"}
