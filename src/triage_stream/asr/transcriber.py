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
from time import perf_counter
import numpy as np

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
        return WhisperModel(settings.whisper_model, device=settings.whisper_device, compute_type=settings.compute_type)

    
    def transcribe_chunk(self, chunk: AudioChunk) -> TranscriptChunk:
      start_time = perf_counter()

      # decode base64 PCM to float32 numpy array
      pcm_bytes = base64.b64decode(chunk.pcm_b64)
      int_16_full = 32767  # max absolute value for int16
      # dividing by int_16_full normalizes the audio samples to the range [-1.0, 1.0], which is a common format for audio processing and is what the ASR model expects as input.
      pcm_np = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32) / int_16_full
      # Update the rolling buffer of bytes with the new chunk

      # Keep a buffer with the latest buffer_seconds of audio
      max_num_samples = int(settings.buffer_seconds * chunk.sample_rate)
      self._buffer = np.concatenate([self._buffer, pcm_np])[-max_num_samples:]

      # Transcribe the current buffer using the model and store in a TranscriptChunk
      segments, _ = self.model.transcribe(self._buffer, beam_size=5)
      segment_json_array = [
          { "start": segment.start, "end": segment.end, "text": segment.text } 
          for segment in segments
      ]
      end_time = perf_counter()

      self._segments.extend(segment_json_array)  # store segments for potential future use (e.g., context for classifier)
      latency_ms = round((end_time - start_time) * 1000, 2) # convert to milliseconds and round to 2 decimal places

      return TranscriptChunk(
          call_id=chunk.call_id,
          seq=chunk.seq,
          ts=chunk.ts,
          text=" ".join(segment_json["text"] for segment_json in segment_json_array),  # concatenate all segment texts for this chunk
          is_partial=not chunk.is_final,
          asr_latency_ms=latency_ms
      )
