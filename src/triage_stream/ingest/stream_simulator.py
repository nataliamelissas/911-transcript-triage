"""Stream simulator: replays sample audio as AudioChunks to mimic a live 911 feed.

WHY simulate: real 911 audio is sensitive PII and cannot go in a public repo.
A simulator over public/synthetic clips gives you the same streaming semantics
(ordering, partials, backpressure) without the compliance problem -- and the
"why" is a great compliance/compartmentalization talking point for the JD.

This will:
  1. Load a sample wav, slice into `settings.chunk_seconds` windows.
  2. Base64-encode each PCM window into an AudioChunk (see schemas.AudioChunk).
  3. Yield chunks on a cadence (asyncio.sleep) to imitate real time.
  4. Emit a final chunk with is_final=True.
Stretch: push to a real queue (Kinesis/Kafka) instead of an in-process generator.
"""
from __future__ import annotations
# Makes all type hints in this file be treated as string literals, which can help with forward references and can improve performance by avoiding the need to evaluate type hints at runtime.

import asyncio
import wave
import base64
import datetime
from collections.abc import AsyncIterator
from triage_stream.common.schemas import AudioChunk
from triage_stream.common.config import settings

async def simulate_call(wav_path: str, call_id: str) -> AsyncIterator[AudioChunk]:
    # Load the wav
    with wave.open(wav_path, "rb") as wav_file:
        curr_seq = 0

        while wav_file.tell() < wav_file.getnframes():  # while there are frames left to read
          # sanity check:
          assert wav_file.getframerate() == 16000, "Expected 16kHz audio for ASR accuracy; resample if needed"
          assert wav_file.getnchannels() == 1, "Expected mono audio for ASR accuracy; downmix if needed"
          assert wav_file.getsampwidth() == 2, "Expected 16-bit PCM for ASR accuracy; convert if needed"

          # Slice into settings.chunk_seconds windows
          frames_per_chunk = int(settings.chunk_seconds * wav_file.getframerate())

          # base64 encode each PCM window into an AudioChunk
          pcm_bytes = wav_file.readframes(frames_per_chunk) # move the file pointer forward by frames_per_chunk and read that chunk of audio data as bytes
          pcm_64 = base64.b64encode(pcm_bytes).decode("ascii")

          # check if last frame
          is_final_frame = wav_file.tell() >= wav_file.getnframes() 

          # create an AudioChunk for this window
          chunk = AudioChunk(
              call_id=call_id,
              seq=curr_seq,
              ts=datetime.now(datetime.timezone.utc),
              # sample_rate=16000, # optional since it's fixed in the config, but good to be explicit in the contract
              pcm_b64=pcm_64,
              is_final=is_final_frame  # set to True on the last chunk
          )
          # Yield chunks on a cadence (asyncio.sleep) to imitate real time
          await asyncio.sleep(settings.chunk_seconds) # simulate real-time delay
          yield chunk

          # Increment sequence number for the next chunk
          curr_seq += 1

          if is_final_frame:
              break  # exit loop after yielding the final chunk
