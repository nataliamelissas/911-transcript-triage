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
1. Get one sample `.wav` (synthesize with a TTS tool, or grab a short public clip) and put it in `data/sample/` (see `data/README.md`). It must be **16 kHz mono 16-bit PCM** — what `AudioChunk` and Whisper assume; convert with `ffmpeg -i clip.mp3 -ar 16000 -ac 1 -sample_fmt s16 call.wav` if needed.
2. Skim the faster-whisper README quickstart (Resources) so you know the API shape.
3. Implement `ingest/stream_simulator.py`: load the wav (stdlib `wave` — gives raw PCM bytes, no extra dependency; `readframes(n)` counts *frames*, not bytes — one frame = one int16 sample = 2 bytes for mono, so `frames_per_chunk = int(getframerate() * settings.chunk_seconds)`; sanity-check `getframerate()==16000`, `getnchannels()==1`, `getsampwidth()==2` first), slice into `settings.chunk_seconds` windows (already in the scaffold: `common/config.py` defines it, default 1.0 s, override via `TS_CHUNK_SECONDS`; import with `from triage_stream.common.config import settings`), base64-encode each PCM window into an `AudioChunk` (contract already in `common/schemas.py`; `pcm_b64 = base64.b64encode(chunk_bytes).decode()` — `b64encode` returns bytes, decode to get the `str` the schema wants since JSON can't carry raw bytes; `seq` = per-chunk counter, `ts = datetime.now(timezone.utc)`), and `yield` them with `asyncio.sleep` to mimic real time; flag the last as `is_final` (set on the last real chunk, not an empty trailer — a short read isn't a reliable signal since files can divide evenly; use `wf.tell() >= wf.getnframes()` after each read, or precompute `math.ceil(total_frames / frames_per_chunk)` and compare `seq`).
4. Implement `asr/transcriber.py`: lazy-load `WhisperModel` (model/device come from `settings.whisper_model` / `settings.whisper_device`, already in `common/config.py`; the `Transcriber` stub with the lazy `_model` slot also exists), decode base64 → float32 numpy (`np.frombuffer(base64.b64decode(pcm_b64), dtype=np.int16).astype(np.float32) / 32768.0` — int16 full scale is 32768, dividing normalizes to −1..1, what `transcribe()` expects), keep a rolling buffer (append each chunk to the call-so-far array and transcribe the accumulated audio; finalize on `is_final`), call `transcribe`, and return a `TranscriptChunk` (contract already in `common/schemas.py`) with `asr_latency_ms` measured.
5. Write a small demo script that pipes the simulator into the transcriber and prints live partial text + per-chunk latency (shape: an `async main()` doing `async for chunk in simulate_call(...)` → `transcribe_chunk(chunk)`, run with `asyncio.run(main())`).
6. Note your P50 latency. Commit: `feat: streaming audio simulator + faster-whisper ASR`.

### Deliverables
- [ ] `stream_simulator.py` emits ordered `AudioChunk`s on a real-time cadence.
- [ ] `transcriber.py` returns `TranscriptChunk`s with latency populated.
- [ ] A demo prints live partials + latency to the console.
- [ ] Day-2 commit pushed.

### Resources
- faster-whisper: https://github.com/SYSTRAN/faster-whisper
- Reading/writing audio (stdlib): https://docs.python.org/3/library/wave.html
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
2. Map its labels to the `Urgency` enum (already in `common/schemas.py`: CRITICAL/HIGH/MODERATE/LOW); make a **stratified** train/val/test split (`sklearn.model_selection.train_test_split`).
3. Tokenize with `AutoTokenizer.from_pretrained("distilbert-base-uncased")`.
4. Fine-tune with `transformers.Trainer`; in `compute_metrics`, report **per-class** precision/recall/F1 (`sklearn.metrics`).
5. Start MLflow: `make up` (or `docker compose up mlflow`); set the tracking URI (`settings.mlflow_tracking_uri`, already in `common/config.py`); `mlflow.log_params/log_metrics` and `mlflow.transformers.log_model(..., name="urgency-classifier", registered_model_name="urgency-classifier")` (MLflow 3: `name`, not `artifact_path`).
6. Add the gate: only set the `@champion` alias (`MlflowClient.set_registered_model_alias`) if critical-class recall ≥ your threshold. Aliases replace the deprecated registry stages; the API loads `models:/urgency-classifier@champion`.
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
- MLflow tracking: https://mlflow.org/docs/latest/ml/tracking/
- MLflow registry workflow (aliases): https://mlflow.org/docs/latest/ml/model-registry/workflow/
- Open dataset option: https://huggingface.co/datasets/community-datasets/disaster_response_messages
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
1. In `classifier/predict.py` (the `UrgencyClassifier` stub and `settings.classifier_model_uri` — `models:/urgency-classifier@champion` — already exist), load the model from the MLflow registry **once at startup** (module-level or FastAPI lifespan), not per request.
2. Implement `classify()`: tokenize → infer → return a `Classification` (contract already in `common/schemas.py`; `score` is validated to 0–1) with `score`, `keywords`, `model_version`, `infer_latency_ms`.
3. Wrap inference in a timeout (`asyncio.wait_for` or a thread with a deadline) using `settings.infer_timeout_ms` (already in `common/config.py`, default 800 ms; `settings.max_retries` is there too); on timeout/exception, call a cheap **keyword-rule fallback** that still returns a `Classification`.
4. Implement `router/router.py` `decide()` (stub already exists): map urgency → `destination` + `suggested_actions`, always `requires_human_confirmation=True` (`RouteDecision` already defaults it to True — never unset it).
5. Wire `POST /classify` and `POST /route` in `api/main.py` (the app with `/healthz` and `/readyz` already exists — you add the endpoints).
6. Add an integration test in `tests/integration/test_api.py` (already exists with a working `/healthz` TestClient example); then deliberately break the model and confirm the fallback path still returns a decision.
7. Commit: `feat: resilient inference + deterministic router + API endpoints`.

### Deliverables
- [ ] `predict.py` loads at startup, enforces timeout, falls back on failure.
- [ ] `router.py` returns a `RouteDecision` with human-confirmation required.
- [ ] `/classify` and `/route` work; integration test passes incl. the fallback case.
- [ ] Day-4 commit pushed.

### Resources
- FastAPI first steps: https://fastapi.tiangolo.com/tutorial/
- FastAPI lifespan (startup load): https://fastapi.tiangolo.com/advanced/events/
- Load an MLflow model: https://mlflow.org/docs/latest/api_reference/python_api/mlflow.pyfunc.html
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
1. Add Prometheus metrics + a request-latency histogram to the API (use `prometheus-fastapi-instrumentator` — already pinned in `requirements.txt` — or a manual `Histogram`).
2. Create `benchmarks/run.py`: replay N sample calls through `/stream`, record end-to-end latency, compute P50/P99 (`np.percentile(latencies, [50, 99])`).
3. Add background noise to your clips (numpy mix — target-SNR math: `gain = (rms_clean / rms_noise) * 10 ** (-snr_db / 20)`, `noisy = np.clip(clean + gain * noise, -1, 1)`, try 20/10/5 dB — or `audiomentations`, already in `requirements.txt`) and re-measure classifier accuracy — report the clean-vs-noisy delta.
4. Write `BENCHMARKS.md` with the actual numbers.
5. Implement `monitoring/drift.py` (the `check_drift()` stub exists; `scipy` is already in `requirements.txt`): persist a training baseline profile, compare recent live stats (KS test via `scipy.stats.ks_2samp`, or use `evidently`), flag drift.
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
1. Build the API image (`Dockerfile` already exists) and define an ECR repo in `infra/terraform/main.tf` (already exists as a commented TODO checklist of the exact resources); push the image.
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
- ECS Fargate with Terraform: https://spacelift.io/blog/terraform-ecs
- ECS on Fargate (AWS blog): https://aws.amazon.com/blogs/developer/provision-aws-infrastructure-using-terraform-by-hashicorp-an-example-of-running-amazon-ecs-tasks-on-aws-fargate/
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
