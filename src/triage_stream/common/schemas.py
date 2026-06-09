"""Shared Pydantic contracts. Define these BEFORE service logic.

Every service (ingest -> asr -> classifier -> router -> api) speaks through
these models. This is the single most important file for keeping the system
decoupled: services depend on the contract, not on each other's internals.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class Urgency(str, Enum):
    CRITICAL = "critical"   # immediate dispatch (e.g., weapon, cardiac arrest)
    HIGH = "high"
    MODERATE = "moderate"
    LOW = "low"


class AudioChunk(BaseModel):
    """A short slice of a call, emitted by the stream simulator."""
    call_id: str
    seq: int = Field(..., description="Monotonic chunk index within a call")
    ts: datetime
    sample_rate: int = 16000
    pcm_b64: str = Field(..., description="Base64-encoded 16-bit PCM mono audio")
    is_final: bool = False


class TranscriptChunk(BaseModel):
    """ASR output for one AudioChunk (may be a partial hypothesis)."""
    call_id: str
    seq: int
    ts: datetime
    text: str
    is_partial: bool = True
    asr_latency_ms: float | None = None


class Classification(BaseModel):
    """Urgency prediction for the transcript so far."""
    call_id: str
    seq: int
    urgency: Urgency
    score: float = Field(..., ge=0.0, le=1.0)
    keywords: list[str] = Field(default_factory=list)
    model_version: str
    infer_latency_ms: float | None = None


class RouteDecision(BaseModel):
    """Final routing decision. A human is always in the loop."""
    call_id: str
    urgency: Urgency
    destination: str  # e.g. "dispatch_fast_path" | "operator_with_suggestions"
    suggested_actions: list[str] = Field(default_factory=list)
    requires_human_confirmation: bool = True
    decided_at: datetime
