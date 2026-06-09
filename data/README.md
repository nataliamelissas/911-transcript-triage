# Data

**Never commit real 911 audio or transcripts.** It is sensitive PII; handling it
correctly (compartmentalization, no public exposure) is part of the JD.

Use a public/synthetic proxy:
- Hugging Face: emergency-call transcript datasets (search "emergency call transcripts").
- Or synthesize: generate labeled transcripts across urgency levels, then TTS to
  audio for the ASR stage.

Put working files in `data/raw/` (gitignored). Commit only a tiny, clearly
synthetic `data/sample/` for tests.
