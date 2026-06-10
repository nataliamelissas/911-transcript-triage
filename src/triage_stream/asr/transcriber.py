"""Streaming ASR using faster-whisper (CTranslate2 backend).

Design notes:
  - faster-whisper is the 2026 default for local low-latency STT.
  - Keep a rolling buffer; transcribe on each chunk to produce partial
    hypotheses, finalize on is_final.
  - Record asr_latency_ms -- you'll need latency benchmarks for the JD.

This will:
  1. Lazy-load WhisperModel(settings.whisper_model, device=settings.whisper_device).
  2. Decode base64 PCM -> float32 numpy.
  3. transcribe() the rolling buffer; return TranscriptChunk.
  4. Measure and attach latency.
"""
from __future__ import annotations

import base64
from functools import cached_property
from time import time
import numpy as np  # Keep this; numpy is lightweight

from triage_stream.common.schemas import AudioChunk, TranscriptChunk
from triage_stream.common.config import settings

class Transcriber:
    def __init__(self) -> None:
        self._model = None  # lazy-load to keep imports cheap
        self._buffer = np.array([], dtype=np.float32)  # rolling buffer for audio samples
        self._segments = []  # store segments for potential future use (e.g., context for classifier)
    
    @cached_property
    def model(self) -> WhisperModel: # type: ignore
        from faster_whisper import WhisperModel  # import here to avoid the heavy dependency if not used
        return WhisperModel(settings.whisper_model, device=settings.whisper_device, compute_type="float16")

    
    def transcribe_chunk(self, chunk: AudioChunk) -> TranscriptChunk:
      start_time = time.perf_counter()

      # decode base64 PCM to float32 numpy array
      pcm_bytes = base64.b64decode(chunk.pcm_b64)
      int_16_full = 32767  # max absolute value for int16
      # dividing by int_16_full normalizes the audio samples to the range [-1.0, 1.0], which is a common format for audio processing and is what the ASR model expects as input.
      pcm_np = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32) / int_16_full
      # Update the rolling buffer of bytes with the new chunk
      self._buffer = np.concatenate([self._buffer, pcm_np])
      # Transcribe only the current buffer chunk using the model and store in a TranscriptChunk
      segments, _ = self.model.transcribe(pcm_np, beam_size=5)

      end_time = time.perf_counter()

      latency_ms = (end_time - start_time) * 1000 # convert to milliseconds
      self._segments.extend(segments)  # store segments for potential future use (e.g., context for classifier)

      return TranscriptChunk(
          call_id=chunk.call_id,
          seq=chunk.seq,
          ts=chunk.ts,
          text=" ".join(segment.text for segment in segments),  # concatenate all segment texts for this chunk
          is_partial=not chunk.is_final,
          asr_latency_ms=latency_ms
      )
