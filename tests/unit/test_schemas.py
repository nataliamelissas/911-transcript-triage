"""Example unit test (the pattern to follow). Fast, isolated, no I/O."""
from datetime import datetime, timezone

from triage_stream.common.schemas import Classification, Urgency


def test_classification_score_bounds() -> None:
    c = Classification(
        call_id="c1", seq=0, urgency=Urgency.CRITICAL,
        score=0.97, model_version="v1",
    )
    assert 0.0 <= c.score <= 1.0
    assert c.urgency is Urgency.CRITICAL


def test_classification_rejects_out_of_range_score() -> None:
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Classification(call_id="c1", seq=0, urgency=Urgency.LOW,
                       score=1.5, model_version="v1")
