"""Train the urgency classifier and log it to MLflow.

Approach: fine-tune a small HF transformer (e.g. distilbert-base-uncased) on
labeled emergency-call transcripts. Track params/metrics/artifacts in MLflow and
register the model so the API can load `models:/urgency-classifier/Production`.

Recall matters more than precision here: a missed CRITICAL is catastrophic.
Optimize and REPORT recall on the critical class, not just accuracy.

TODO(you):
  1. Load dataset (see data/README.md) -> train/val/test split (stratified).
  2. Tokenize, fine-tune with transformers.Trainer.
  3. mlflow.log_params / log_metrics (per-class precision/recall/F1, latency).
  4. mlflow.transformers.log_model(..., registered_model_name="urgency-classifier").
  5. Add a quality GATE: only register if critical-class recall >= threshold.
"""
from __future__ import annotations


def main() -> None:
    raise NotImplementedError("Day 3: fine-tune + MLflow tracking + registry gate")


if __name__ == "__main__":
    main()
