# 7-Day Study + Build Plan — `triage-stream`

**Goal:** ship a production-shaped, real-time 911-transcript triage system you can
explain end-to-end in your next two technical interviews — and link on GitHub.

**Budget:** 1–2 hrs/evening × 7 = ~7–14 hrs. Sequenced so that if an evening runs
short you still have a working system; the Day 7 AWS deploy is the one stretch.

**Honest scope:** this budget builds a complete, tested, observable pipeline that
runs locally and deploys one real AWS slice — *not* K8s + Airflow + Ray. That's
more credible than a half-finished distributed system. The "after the interviews"
section is your "how would this scale?" answer.

---

## What you already have (your toolbox)

The repo is scaffolded — you are filling in logic, not starting from a blank page.

- **Contracts:** `src/triage_stream/common/schemas.py` — the data models every stage passes. Read this first.
- **Config & logging:** `common/config.py` (env-based settings), `common/logging.py` (JSON logs). Done for you.
- **Stubs to implement:** every file with a `TODO(you)` marker — run `grep -rn "TODO(you)" src` to list them all.
- **Commands:** `Makefile` — `make install`, `make test-unit`, `make test`, `make run-api`, `make train`, `make up` (docker compose).
- **Local infra:** `docker-compose.yml` brings up MLflow (model registry) + the API. `Dockerfile` builds the API image.
- **CI:** `.github/workflows/ci.yml` runs lint + type + unit tests on every push.
- **Concept reference:** `PRINCIPLES.md` — the "why" behind each piece, for interview prep.

**How to use each day:** read the **Description**, follow the **Steps** in order,
tick the **Deliverables**, and use the **Resources** when stuck. A day is done only
when every checkbox is ticked. `⭐` = a gap your screener already exposed.

---

## Day 1 — Foundations, contracts, and the acceptance test

**Description:** Get the project running, understand the data contracts, and write
the one test that defines "done" for the whole system. No feature code yet — today
is about orientation and a clear target.

### Learning objectives
- [ ] ⭐ Define unit vs integration vs e2e precisely (scope, speed, count, what's mocked).
- [ ] Explain the **test pyramid** vs the **outside-in / acceptance-first** approach, and when each applies.
- [ ] Explain why contracts (Pydantic models) are defined before any service logic.

### Steps
1. Create a Python 3.10+ virtualenv and run `make install`.
2. Run `make test-unit` — confirm the green baseline (the example schema tests pass).
3. Open `common/schemas.py` and read every model. On paper, draw the flow: `AudioChunk → TranscriptChunk → Classification → RouteDecision`.
4. Read the test-pyramid article (Resources); write 3 sentences distinguishing unit/integration/e2e in your own words.
5. In `tests/e2e/test_pipeline.py`, replace the `skip` with an `xfail` test that asserts "a critical sample call routes to `dispatch_fast_path`." It won't pass yet — that's the point; you're defining the target API.
6. Commit: `test: add acceptance test for critical-call routing`.

### Deliverables
- [ ] `make install` succeeds and `make test-unit` is green.
- [ ] You can verbally walk every model in `schemas.py`.
- [ ] An xfail e2e test exists describing the critical-call path.
- [ ] Day-1 commit pushed (CI runs).

### Resources
- Test pyramid: https://martinfowler.com/articles/practical-test-pyramid.html
- pytest basics: https://docs.pytest.org/en/stable/how-to/index.html
- Repo: `common/schemas.py`, `tests/`

**Interview payoff:** "I start from an acceptance test that defines done, then drive units inward — and keep e2e few because they're slow and brittle."

---

## Day 2 — Streaming ingest + ASR

**Description:** Build the front of the pipeline: a simulator that replays audio as
a live stream, and an ASR component that turns those chunks into transcripts with
measured latency.

### Learning objectives
- [ ] Explain streaming STT: chunking, partial vs final hypotheses, rolling buffer.
- [ ] Explain the latency/accuracy tradeoff and why chunk length is the knob (~1s ≈ 500–800ms).
- [ ] Explain why you simulate the stream instead of using real 911 audio (PII / compartmentalization).

### Steps
1. Get one sample `.wav` (synthesize with a TTS tool, or grab a short public clip) and put it in `data/sample/` (see `data/README.md`).
2. Skim the faster-whisper README quickstart (Resources) so you know the API shape.
3. Implement `ingest/stream_simulator.py`: load the wav (`soundfile`/`wave`), slice into `settings.chunk_seconds` windows, base64-encode each PCM window into an `AudioChunk`, and `yield` them with `asyncio.sleep` to mimic real time; flag the last as `is_final`.
4. Implement `asr/transcriber.py`: lazy-load `WhisperModel`, decode base64 → float32 numpy, keep a rolling buffer, call `transcribe`, and return a `TranscriptChunk` with `asr_latency_ms` measured.
5. Write a small demo script that pipes the simulator into the transcriber and prints live partial text + per-chunk latency.
6. Note your P50 latency. Commit: `feat: streaming audio simulator + faster-whisper ASR`.

### Deliverables
- [ ] `stream_simulator.py` emits ordered `AudioChunk`s on a real-time cadence.
- [ ] `transcriber.py` returns `TranscriptChunk`s with latency populated.
- [ ] A demo prints live partials + latency to the console.
- [ ] Day-2 commit pushed.

### Resources
- faster-whisper: https://github.com/SYSTRAN/faster-whisper
- Reading/writing audio: https://python-soundfile.readthedocs.io/
- Repo: `ingest/stream_simulator.py`, `asr/transcriber.py`, `schemas.py`

**Interview payoff:** real numbers — "P50 ASR latency was ~X ms at 1s chunks."

---

## Day 3 — The model: train, track, register (MLOps core)

**Description:** Train the urgency classifier, track the experiment in MLflow, and
register it only if it clears a recall bar. This is the heart of the MLOps story.

### Learning objectives
- [ ] ⭐ Explain why **critical-class recall** is the gating metric, not accuracy (cost of a false negative).
- [ ] Distinguish MLflow **tracking** vs **registry** vs **serving**.
- [ ] Explain transfer learning / fine-tuning a small transformer and stratified splits.

### Steps
1. Get a public/synthetic emergency-transcript dataset (`data/README.md`) and load it with HF `datasets`.
2. Map its labels to the `Urgency` enum; make a **stratified** train/val/test split (`sklearn.model_selection.train_test_split`).
3. Tokenize with `AutoTokenizer.from_pretrained("distilbert-base-uncased")`.
4. Fine-tune with `transformers.Trainer`; in `compute_metrics`, report **per-class** precision/recall/F1 (`sklearn.metrics`).
5. Start MLflow: `make up` (or `docker compose up mlflow`); set the tracking URI; `mlflow.log_params/log_metrics` and `mlflow.transformers.log_model(..., registered_model_name="urgency-classifier")`.
6. Add the gate: only register/promote if critical-class recall ≥ your threshold.
7. Open `localhost:5000`, confirm the run + registered model. Commit: `feat: train + MLflow tracking + recall-gated registry`.

### Deliverables
- [ ] Dataset placed (no real PII committed).
- [ ] `train.py` fine-tunes and logs per-class metrics to MLflow.
- [ ] Model registers only when critical recall clears the threshold.
- [ ] Run + model visible at `localhost:5000`; Day-3 commit pushed.

### Resources
- HF fine-tuning: https://huggingface.co/docs/transformers/training
- HF datasets: https://huggingface.co/docs/datasets/loading
- Metrics: https://scikit-learn.org/stable/modules/model_evaluation.html
- MLflow tracking: https://mlflow.org/docs/latest/tracking.html
- MLflow registry: https://mlflow.org/docs/latest/model-registry.html
- Repo: `classifier/train.py`, `data/README.md`

**Interview payoff:** "I gate promotion on critical-class recall — accuracy hides the failure that actually hurts."

---

## Day 4 — Serving with resilience + routing

**Description:** Stand up the serving layer that loads the model, classifies text,
and routes — with timeouts and a fallback so it degrades instead of failing.

### Learning objectives
- [ ] ⭐ Explain timeouts, retries, and graceful degradation as concrete code, not buzzwords.
- [ ] Explain "model scores, policy decides" and why the router is deterministic + unit-tested.
- [ ] Explain loading the model once at startup vs per-request, and async serving.

### Steps
1. In `classifier/predict.py`, load the model from the MLflow registry **once at startup** (module-level or FastAPI lifespan), not per request.
2. Implement `classify()`: tokenize → infer → return a `Classification` with `score`, `keywords`, `model_version`, `infer_latency_ms`.
3. Wrap inference in a timeout (`asyncio.wait_for` or a thread with a deadline) using `settings.infer_timeout_ms`; on timeout/exception, call a cheap **keyword-rule fallback** that still returns a `Classification`.
4. Implement `router/router.py` `decide()`: map urgency → `destination` + `suggested_actions`, always `requires_human_confirmation=True`.
5. Wire `POST /classify` and `POST /route` in `api/main.py`.
6. Add an integration test in `tests/integration/test_api.py`; then deliberately break the model and confirm the fallback path still returns a decision.
7. Commit: `feat: resilient inference + deterministic router + API endpoints`.

### Deliverables
- [ ] `predict.py` loads at startup, enforces timeout, falls back on failure.
- [ ] `router.py` returns a `RouteDecision` with human-confirmation required.
- [ ] `/classify` and `/route` work; integration test passes incl. the fallback case.
- [ ] Day-4 commit pushed.

### Resources
- FastAPI first steps: https://fastapi.tiangolo.com/tutorial/
- FastAPI lifespan (startup load): https://fastapi.tiangolo.com/advanced/events/
- Load an MLflow model: https://mlflow.org/docs/latest/python_api/mlflow.pyfunc.html
- Repo: `classifier/predict.py`, `router/router.py`, `api/main.py`

**Interview payoff:** "It fails predictably — timeout → keyword fallback → human-in-the-loop. It degrades, it doesn't drop."

---

## Day 5 — End-to-end streaming path (turn Day 1 green)

**Description:** Connect every stage behind a WebSocket so a streamed call produces
live routing decisions — and make your Day-1 acceptance test pass.

### Learning objectives
- [ ] Explain WebSocket streaming in FastAPI and basic backpressure.
- [ ] Explain how the full path composes: audio → ASR → classify → route.

### Steps
1. Add a `WS /stream` endpoint in `api/main.py`.
2. For each incoming `AudioChunk`: transcribe (Day 2) → classify (Day 4) → decide (Day 4); send the `RouteDecision` back as JSON.
3. Handle `is_final` (finalize the transcript) and client disconnects cleanly.
4. Update `tests/e2e/test_pipeline.py` to stream a known **critical** sample through the endpoint and assert `dispatch_fast_path`; remove the `xfail`.
5. Run `make test` — everything green (unit + integration + e2e).
6. Do a manual demo and watch decisions update live. Commit: `feat: end-to-end streaming pipeline (e2e green)`.

### Deliverables
- [ ] `WS /stream` streams `AudioChunk`s in and `RouteDecision`s out.
- [ ] The Day-1 e2e test passes.
- [ ] `make test` fully green; manual demo works.
- [ ] Day-5 commit pushed.

### Resources
- FastAPI WebSockets: https://fastapi.tiangolo.com/advanced/websockets/
- Testing WebSockets: https://fastapi.tiangolo.com/advanced/testing-websockets/
- Repo: `api/main.py`, `tests/e2e/test_pipeline.py`

**Interview payoff:** you can demo the whole system and walk any layer on request.

---

## Day 6 — Observability, benchmarks, hardening

**Description:** Make the system measurable: add metrics, produce real latency and
noisy-audio numbers, and add a drift check. These numbers are your differentiator.

### Learning objectives
- [ ] Explain the four golden signals (latency, traffic, errors, saturation).
- [ ] Explain ASR eval (WER) and why you stratify accuracy by noise level.
- [ ] ⭐ Explain drift and why it breaks models ~3 months in (PSI / KS test).

### Steps
1. Add Prometheus metrics + a request-latency histogram to the API (use `prometheus-fastapi-instrumentator` for speed, or a manual `Histogram`).
2. Create `benchmarks/run.py`: replay N sample calls through `/stream`, record end-to-end latency, compute P50/P99.
3. Add background noise to your clips (numpy mix, or `audiomentations`) and re-measure classifier accuracy — report the clean-vs-noisy delta.
4. Write `BENCHMARKS.md` with the actual numbers.
5. Implement `monitoring/drift.py`: persist a training baseline profile, compare recent live stats (KS test via `scipy.stats.ks_2samp`, or use `evidently`), flag drift.
6. Commit: `feat: metrics + latency/noise benchmarks + drift monitor`.

### Deliverables
- [ ] API exposes Prometheus metrics + latency histogram.
- [ ] `BENCHMARKS.md` with measured P50/P99 latency and noisy-audio accuracy.
- [ ] `drift.py` does a working baseline-vs-live comparison.
- [ ] Day-6 commit pushed.

### Resources
- Golden signals: https://sre.google/sre-book/monitoring-distributed-systems/
- FastAPI Prometheus: https://github.com/trallnag/prometheus-fastapi-instrumentator
- Audio augmentation: https://github.com/iver56/audiomentations
- Drift (KS test): https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ks_2samp.html
- Repo: `monitoring/drift.py`, `api/main.py`

**Interview payoff:** "Here are my measured latency and noisy-audio accuracy numbers" — almost no candidate brings these.

---

## Day 7 — Deploy one AWS slice + polish

**Description:** Put one real piece in the cloud with infrastructure-as-code, prove
it's reachable, tear it down, and finalize the README. Then you can say "it's
deployed."

### Learning objectives
- [ ] Explain ECS Fargate vs Lambda-container for model serving (cold start vs always-on, cost).
- [ ] Explain why infra is in code (Terraform) and what a remote state backend buys you.

### Steps
1. Build the API image (`Dockerfile` already exists) and define an ECR repo in `infra/terraform/main.tf`; push the image.
2. Define the runtime: a Fargate service (always-on) **or** the classifier as a Lambda container image (serverless), plus a CloudWatch log group.
3. `terraform init` → `plan` → `apply`; hit the deployed `/healthz`.
4. `terraform destroy` to avoid ongoing cost.
5. Finalize `README.md`: architecture diagram + your Day-6 benchmark numbers + a note that it's deployable on demand.
6. Commit: `feat: AWS deploy via Terraform + final README`.

### Deliverables
- [ ] `main.tf` provisions ECR + Fargate/Lambda + CloudWatch.
- [ ] Deployed `/healthz` responds; `terraform destroy` works.
- [ ] `README.md` finalized with diagram + benchmarks.
- [ ] Day-7 commit pushed.

### Resources
- Terraform AWS provider: https://registry.terraform.io/providers/hashicorp/aws/latest/docs
- ECS Fargate (Terraform): https://developer.hashicorp.com/terraform/tutorials/aws/aws-ecs
- Lambda container images: https://docs.aws.amazon.com/lambda/latest/dg/images-create.html
- Repo: `infra/terraform/main.tf`, `Dockerfile`, `README.md`

**Interview payoff:** "It's deployed on AWS with IaC — here's the endpoint and the teardown."

---

## After the interviews — your "how would this scale?" answer
Real streaming bus (Kinesis/Kafka) replacing the in-process generator; horizontal
scaling on K8s; Airflow/Temporal for retraining orchestration; Ray for distributed
inference/training; a feature store; canary deploys with auto-rollback on metric
regression; a model cascade (fast model on every chunk, escalate ambiguous cases).
Naming these *as deliberately deferred* shows judgment — you scoped for the
deadline and know the production path.

## Map to the job description
Python/SQL · containerized (Docker) + serverless (Lambda) + cloud (AWS) · MLOps
full lifecycle (train→register→serve→monitor) · latency & noisy-audio benchmarks ·
data security/compartmentalization (no PII) · resilient real-time streaming ·
CI/CD (GitHub Actions) · testing methodology.
