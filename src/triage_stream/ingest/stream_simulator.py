"""Stream simulator: replays sample audio as AudioChunks to mimic a live 911 feed.

WHY simulate: real 911 audio is sensitive PII and cannot go in a public repo.
A simulator over public/synthetic clips gives you the same streaming semantics
(ordering, partials, backpressure) without the compliance problem -- and the
"why" is a great compliance/compartmentalization talking point for the JD.

TODO(you):
  1. Load a sample wav, slice into `settings.chunk_seconds` windows.
  2. Base64-encode each PCM window into an AudioChunk (see schemas.AudioChunk).
  3. Yield chunks on a cadence (asyncio.sleep) to imitate real time.
  4. Emit a final chunk with is_final=True.
Stretch: push to a real queue (Kinesis/Kafka) instead of an in-process generator.
"""
from __future__ import annotations

from collections.abc import AsyncIterator

from triage_stream.common.schemas import AudioChunk


async def simulate_call(wav_path: str, call_id: str) -> AsyncIterator[AudioChunk]:
    raise NotImplementedError("Day 2: implement the audio stream simulator")
