# Principles to Review

The concepts this project is built to teach, grouped into the three areas your
interviews will probe. Each: **what it is → where in the repo → why they ask.**
Priority markers: ⭐ = a gap your screener already exposed; review these first.

---

## 1. MLOps

**Full ML lifecycle** — data → train → eval → **registry** → serve → monitor →
retrain, each step automated.
*Where:* `classifier/train.py`, `predict.py`, `monitoring/drift.py`, CI.
*Why:* the JD says "full ML lifecycle from prototype to production." Be able to
draw the loop and name the tool at each stage.

**Tracking vs registry vs serving** — three distinct things people conflate.
Tracking = experiment runs/metrics (MLflow Tracking). Registry = versioned
models, with the deployable one marked by an *alias* (stages are deprecated).
Serving = the runtime that loads a registry model.
*Where:* `train.py` logs runs; API loads `models:/urgency-classifier@champion`.
*Why:* sloppy candidates say "MLflow" as one blob; precision signals seniority.

⭐ **Promotion gates on the *right* metric** — register only if **critical-class
recall ≥ threshold**, not accuracy. A missed `CRITICAL` is catastrophic, so you
trade precision for recall deliberately.
*Where:* gate in `train.py`; `Urgency`/`score` in `schemas.py`.
*Why:* shows you reason about the *cost of errors*, not vanity metrics.

**Reproducibility & versioning** — every prediction carries `model_version`;
config is externalized; runs are logged.
*Where:* `Classification.model_version`, `common/config.py`.
*Why:* "which model produced this output?" must be answerable in production.

⭐ **Evaluation & benchmarking** — latency P50/P99 and accuracy on **noisy
audio**, reported as numbers.
*Where:* Day 6 `benchmarks/`, `asr_latency_ms` / `infer_latency_ms` fields.
*Why:* JD asks for "latency benchmarks, noisy audio, accuracy." Bring measured
numbers — almost no candidate does.

**Drift monitoring** — compare live input distribution vs training baseline
(PSI / KS); the thing that silently breaks models in month 3.
*Where:* `monitoring/drift.py`.
*Why:* the #1 "what did you forget" question in MLOps interviews.

⭐ **Model selection & cascade** — match model to task: a small fast model on
every chunk, escalate only ambiguous cases to a bigger one; know when *not* to
use an LLM at all. (Your screener's point: Haiku, not Opus, for streaming.)
*Where:* fallback in `predict.py`; "deferred" cascade in README/STUDY_PLAN.
*Why:* this is the exact reasoning you got corrected on. Own it.

**Graceful model degradation** — inference timeout → cheap keyword fallback, so a
slow/down model never drops a call.
*Where:* `predict.py` (timeout + fallback).
*Why:* MLOps reliability — the model is a dependency that *will* fail.

---

## 2. Secure & Testable System Design

⭐ **Testing taxonomy + pyramid** — unit (isolated, many, fast) / integration
(real seams) / e2e (whole system, few, slow). Plus the **outside-in /
acceptance-first** approach (write the e2e test that defines "done," drive units
inward) — know both and when each applies.
*Where:* `tests/unit|integration|e2e`; e2e written Day 1, green Day 5.
*Why:* you fumbled this live. Define all three crisply and defend pyramid vs
outside-in as a *choice*, not dogma.

**Contracts first** — define the Pydantic models every service speaks before any
logic; validate at boundaries.
*Where:* `common/schemas.py`.
*Why:* decoupling + input validation; "most PoCs break where services talk."

⭐ **Resilience patterns** — timeouts, retries with backoff, circuit breakers,
idempotency, graceful degradation. (These are literally your own stated
engineering principles — make them concrete here.)
*Where:* `config.py` (timeout/retries), `predict.py` (fallback).
*Why:* "a scalable system fails predictably and recovers quickly." Show it.

**Observability** — structured (JSON) logging, the four golden signals
(latency/traffic/errors/saturation), tracing, health/readiness probes.
*Where:* `common/logging.py`, `api/main.py` (`/healthz`, `/readyz`), Day 6 metrics.
*Why:* "how do you know it's healthy in prod?" — probes + metrics, not vibes.

**12-factor config & secrets** — config from env, never hardcoded; no secrets in
the repo.
*Where:* `common/config.py` (pydantic-settings), `.env.example`, `.gitignore`.
*Why:* basic security hygiene interviewers spot-check.

**Security & data compartmentalization** — input validation, least privilege,
RBAC, audit logging, dependency scanning, and **no real 911 PII in the repo**.
*Where:* `data/README.md` (PII policy), simulated stream.
*Why:* JD: "security, compliance, compartmentalization for public-safety data."
Your "why I simulate the stream" answer *is* a compliance answer.

**Human-in-the-loop for high-stakes decisions** — automation suggests; a person
confirms.
*Where:* `RouteDecision.requires_human_confirmation`.
*Why:* public safety can't fully auto-dispatch on a model call; shows judgment.

**Separation of concerns** — the model *scores*; a deterministic, unit-tested
policy *decides*.
*Where:* `classifier/` vs `router/router.py`.
*Why:* keeps the high-stakes decision auditable and testable.

**CI/CD + IaC** — lint + type + test as merge gates; reproducible infra in code.
*Where:* `.github/workflows/ci.yml`, `Makefile`, `infra/terraform/`.
*Why:* JD requires CI/CD (GitHub Actions). "Automate deployment and infra."

---

## 3. NLP / ML Architecture

⭐ **Streaming ASR** — chunking, **partial vs final hypotheses**, rolling buffer,
and the **latency/accuracy tradeoff** (chunk length is the knob: ~1s ≈ 500–800ms
latency).
*Where:* `asr/transcriber.py`, `ingest/stream_simulator.py`, `TranscriptChunk.is_partial`.
*Why:* the core of their product; "stream transcripts to a service" was your
live design question.

**Two-stage ASR → NLU pipeline** — transcribe, then classify; each stage swappable.
*Where:* `asr/` → `classifier/`.
*Why:* the standard architecture for spoken-language understanding.

**Transfer learning / fine-tuning** — adapt a small pretrained transformer
(DistilBERT) with tokenization rather than training from scratch.
*Where:* `classifier/train.py`.
*Why:* "experience with ML frameworks / HF"; know why fine-tune > from-scratch.

⭐ **Class imbalance & metric choice** — rare critical class → stratified splits,
recall focus, threshold tuning; for ASR, **WER** stratified by noise/accent.
*Where:* `train.py` eval; Day 6 noisy benchmarks.
*Why:* the substance behind "optimize accuracy to meet system requirements."

**Lightweight fallback (rules / keyword / NER)** — a fast deterministic layer
that also serves as the degradation path.
*Where:* keyword fallback in `predict.py`.
*Why:* knowing when a rule beats a model = maturity.

**Real-time constraints** — latency budgets per stage, backpressure on the stream.
*Where:* `config.infer_timeout_ms`, WS `/stream` (Day 5).
*Why:* "controlling feature scope in real-time streaming solutions" (JD).

**Model cascade for cost/latency** — cheap model first, escalate ambiguous cases.
*Where:* README "deferred"; ties back to the Haiku/Sonnet/Opus reasoning.
*Why:* connects NLP design to cost — a senior-level concern.

---

## Review order given your interviews
1. ⭐ Testing taxonomy + pyramid (§2) — the easiest gap to fully close.
2. ⭐ Model selection / cascade + why recall (§1, §3) — you were corrected here.
3. ⭐ Resilience + observability (§2) — turns "we test manually" into a real answer.
4. Streaming ASR mechanics (§3) — the heart of their product.
5. Drift + benchmarking (§1) — the "what most people forget" differentiators.
