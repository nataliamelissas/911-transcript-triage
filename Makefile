.PHONY: install lint type test test-unit run-api train up down convert
install:    ; pip install -r requirements.txt && pip install -e .
lint:       ; ruff check src tests
type:       ; mypy src
test-unit:  ; pytest tests/unit -q
test:       ; pytest -q
run-api:    ; uvicorn triage_stream.api.main:app --reload --port 8000
train:      ; python -m triage_stream.classifier.train
up:         ; docker compose up --build
down:       ; docker compose down
convert:    ; python -m triage_stream.utils.convert_wav_to_16k ${IN-data/sample/call_10.wav} ${OUT-data/sample/call_10_16k.wav}
