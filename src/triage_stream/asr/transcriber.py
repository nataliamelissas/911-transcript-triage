"""Streaming ASR using faster-whisper (CTranslate2 backend).

Design notes:
  - faster-whisper is the 2026 default for local low-latency STT.
  - Keep a rolling buffer; transcribe on each chunk to produce partial
    hypotheses, finalize on is_final.
  - Record asr_latency_ms -- you'll need latency benchmarks for the JD.

TODO(you):
  1. Lazy-load WhisperModel(settings.whisper_model, device=settings.whisper_device).
  2. Decode base64 PCM -> float32 numpy.
  3. transcribe() the rolling buffer; return TranscriptChunk.
  4. Measure and attach latency.
"""
from __future__ import annotations

from triage_stream.common.schemas import AudioChunk, TranscriptChunk


class Transcriber:
    def __init__(self) -> None:
        self._model = None  # lazy-load to keep imports cheap

    def transcribe_chunk(self, chunk: AudioChunk) -> TranscriptChunk:
        raise NotImplementedError("Day 2: implement faster-whisper streaming")
