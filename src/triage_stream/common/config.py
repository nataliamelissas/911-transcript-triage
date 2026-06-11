"""Centralized config via pydantic-settings. 12-factor: config from env."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="TS_", extra="ignore")

    # ASR
    whisper_model: str = "base.en"      # tiny.en for CPU speed; base.en for accuracy
    whisper_device: str = "cpu"         # "cuda" if you have a GPU
    compute_type: str = "float32"       # "int8" for faster inference with some accuracy tradeoff; requires compatible hardware (e.g. 4th gen Intel or Nvidia T4+ GPUs)
    chunk_seconds: float = 1.0          # streaming chunk length -> latency knob
    buffer_seconds: float = 60.0        # how much audio to keep in the rolling buffer for context

    # Classifier
    # Alias-based registry URI (registry *stages* are deprecated since MLflow 2.9;
    # you mark the deployable version with an alias, e.g. "champion")
    classifier_model_uri: str = "models:/urgency-classifier@champion"
    mlflow_tracking_uri: str = "http://localhost:5000"

    # Resilience (you list these in your own engineering principles)
    infer_timeout_ms: int = 800
    max_retries: int = 2

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000


settings = Settings()
