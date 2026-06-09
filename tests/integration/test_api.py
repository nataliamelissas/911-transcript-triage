"""Integration tests: real FastAPI app via TestClient (tests the wiring)."""
from fastapi.testclient import TestClient

from triage_stream.api.main import app

client = TestClient(app)


def test_healthz() -> None:
    assert client.get("/healthz").json() == {"status": "ok"}


# TODO(you): POST /classify and /route once wired; assert contract + status.
