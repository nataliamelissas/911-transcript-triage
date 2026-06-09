"""E2E: simulated call audio in -> RouteDecision out, through every stage.

TODO(you): feed a known 'critical' sample clip through the WS /stream endpoint
and assert it routes to dispatch_fast_path. This is your outside-in acceptance
test -- write it early to define 'done', then drive units inward.
"""
import pytest


@pytest.mark.e2e
def test_critical_call_routes_to_fast_path() -> None:
    pytest.xfail("Day 5: implement the end-to-end streaming path first")
