# triage-stream

> **Note:** The scaffold and initial structure were generated with AI assistance. All subsequent implementation is written by hand without AI, except for minor IDE autocompletions. This is a learning project.

Real-time **911-transcript triage**: streaming audio → ASR → urgency
classification → routing, built to production-engineering standards. A portfolio
project mirroring the kind of system public-safety AI teams build.

> **Why this exists:** emergency calls are time-critical and language/ordering
> matter. This system streams call audio, transcribes it live, scores urgency,
> and routes — fast path to dispatch for critical calls, operator with suggested
> next steps otherwise — always with a human in the loop.

## Architecture

```
                +-------------------+
 sample audio   |  ingest /         |  AudioChunk (base64 PCM, ordered, partial)
 (no real PII) ->|  stream_simulator|------------------+
                +-------------------+                  v
                                          +-------------------------+
                                          | asr / transcriber       |  faster-whisper
                                          | rolling buffer, partials|  (streaming STT)
                                          +-----------+-------------+
                                                      | TranscriptChunk
                                                      v
                                          +-------------------------+
                                          | classifier / predict    |  HF model from
                                          | timeout + keyword       |  MLflow registry
                                          | fallback (degrades)     |
                                          +-----------+-------------+
                                                      | Classification (urgency, score)
                                                      v
                                          +-------------------------+
                                          | router / decide         |  deterministic,
                                          | human-in-the-loop       |  testable policy
                                          +-----------+-------------+
                                                      | RouteDecision
                                                      v
                                   FastAPI  (REST + WS /stream, metrics, health)
                                                      |
                MLflow (tracking + model registry)    +--> AWS slice (ECS/Lambda + IaC)
```

## Design decisions (and the tradeoffs)

- **Simulated stream over real 911 audio.** Real recordings are sensitive PII and
  cannot live in a public repo. A simulator over public/synthetic clips preserves
  the streaming semantics (ordering, partials, backpressure) without the
  compliance risk. _Compartmentalization of sensitive data is a feature, not a
  shortcut._
- **`faster-whisper` for ASR.** 2026 default for low-latency local STT
  (CTranslate2, INT8/FP16). Chunk length is the latency/accuracy knob.
- **Small fine-tuned classifier, recall-optimized.** A missed `CRITICAL` is
  catastrophic, so the registry promotion gate is on **critical-class recall**,
  not accuracy. (In production you'd add a model _cascade_: a fast model on every
  chunk, escalating only ambiguous cases to a larger one.)
- **Model scores, policy decides.** Routing is deterministic and unit-tested,
  kept out of the model so it's auditable.
- **Fails predictably.** Inference has a timeout and a keyword-rule fallback;
  the system degrades to the operator instead of dropping a call. Human
  confirmation is always required.
- **Pydantic contracts first.** Every stage speaks through `common/schemas.py`,
  so services stay decoupled.

## Quickstart

```bash
make install            # deps + editable install
.\Scripts\Activate.ps1  # activates venv
make test-unit          # fast unit tests (start here)
docker compose up       # mlflow registry + api locally
make run-api            # API at http://localhost:8000  (/docs for Swagger)
```

## Status

Scaffold + contracts + CI in place. Core logic is built across a 7-day plan —
see **[STUDY_PLAN.md](STUDY_PLAN.md)**.

## Tech

Python · FastAPI · Pydantic · faster-whisper · Hugging Face Transformers · MLflow
· Docker · GitHub Actions · Terraform (AWS) · pytest / ruff / mypy.

## Scaling path (deliberately deferred)

Real streaming bus (Kinesis/Kafka), Kubernetes, Airflow/Temporal for retraining,
Ray for distributed inference, feature store, canary + auto-rollback. Scoped out
to ship a complete system on a deadline; this is the production roadmap.
