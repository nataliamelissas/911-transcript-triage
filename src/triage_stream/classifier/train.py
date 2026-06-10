"""Train the urgency classifier and log it to MLflow.

Approach: fine-tune a small HF transformer (e.g. distilbert-base-uncased) on
labeled emergency-call transcripts. Track params/metrics/artifacts in MLflow,
register the model, and mark the deployable version with the "champion" alias
so the API can load `models:/urgency-classifier@champion`. (Registry *stages*
like /Production are deprecated since MLflow 2.9 -- aliases replace them.)

Recall matters more than precision here: a missed CRITICAL is catastrophic.
Optimize and REPORT recall on the critical class, not just accuracy.

TODO(you):
  1. Load dataset (see data/README.md) -> train/val/test split (stratified).
  2. Tokenize, fine-tune with transformers.Trainer.
  3. mlflow.log_params / log_metrics (per-class precision/recall/F1, latency).
  4. mlflow.transformers.log_model(..., name="urgency-classifier",
     registered_model_name="urgency-classifier").  # MLflow 3: name, not artifact_path
  5. Add a quality GATE: only set the "champion" alias if critical-class recall
     >= threshold (MlflowClient.set_registered_model_alias).
"""
from __future__ import annotations


def main() -> None:
    raise NotImplementedError("Day 3: fine-tune + MLflow tracking + registry gate")


if __name__ == "__main__":
    main()
