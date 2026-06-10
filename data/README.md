# Data

**Never commit real 911 audio or transcripts.** It is sensitive PII; handling it
correctly (compartmentalization, no public exposure) is part of the JD.

Use a public/synthetic proxy. Open 911-call datasets are essentially
unavailable (the few on HF are gated), so the realistic options are:

- **Synthesize (primary path):** generate labeled transcripts across all four
  urgency levels — it's the only way to guarantee clean `CRITICAL` examples —
  then TTS them to audio for the ASR stage.
- **Real proxy datasets (verified open, June 2026):**
  - [disaster_response_messages](https://huggingface.co/datasets/community-datasets/disaster_response_messages)
    — ~26k real disaster messages with category labels you can map to `Urgency`.
  - [healthcare call-center transcripts](https://huggingface.co/datasets/urvog/llama2_transcripts_healthcare_callcenter)
    — call-shaped dialogue if you want conversational structure.

**Audio format:** the `AudioChunk` contract and Whisper both assume
**16 kHz, mono, 16-bit PCM** WAV. Convert anything else first:
`ffmpeg -i clip.mp3 -ar 16000 -ac 1 -sample_fmt s16 data/sample/call.wav`

Put working files in `data/raw/` (gitignored). Commit only a tiny, clearly
synthetic `data/sample/` for tests.
