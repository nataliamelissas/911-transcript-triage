"""Routing policy. Deterministic and testable -- NOT an ML model.

Keep policy out of the model: the model scores urgency, the router decides what
to do with that score. That separation is easy to unit-test and to audit.

TODO(you):
  1. CRITICAL/HIGH -> dispatch_fast_path with suggested_actions.
  2. MODERATE/LOW -> operator_with_suggestions.
  3. ALWAYS set requires_human_confirmation=True (human-in-the-loop).
"""
from __future__ import annotations

from triage_stream.common.schemas import Classification, RouteDecision


def decide(c: Classification) -> RouteDecision:
    raise NotImplementedError("Day 4: implement routing policy")
