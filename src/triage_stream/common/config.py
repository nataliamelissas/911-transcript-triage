"""Centralized config via pydantic-settings. 12-factor: config from env."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="TS_", extra="ignore")

    # ASR
    whisper_model: str = "base.en"      # tiny.en for CPU speed; base.en for accuracy
    whisper_device: str = "cpu"         # "cuda" if you have a GPU
    chunk_seconds: float = 1.0          # streaming chunk length -> latency knob

    # Classifier
    classifier_model_uri: str = "models:/urgency-classifier/Production"
    mlflow_tracking_uri: str = "http://localhost:5000"

    # Resilience (you list these in your own engineering principles)
    infer_timeout_ms: int = 800
    max_retries: int = 2

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000


settings = Settings()
