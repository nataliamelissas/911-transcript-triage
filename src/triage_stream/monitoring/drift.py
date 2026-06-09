"""Drift monitor: compare live input distribution vs the training baseline.

The component most PoCs skip -- and the one that breaks models 3 months in.

TODO(you):
  1. Persist a training-baseline profile (e.g. transcript length, token stats,
     class-balance of predictions).
  2. On a schedule, compute the same stats on recent live data.
  3. Flag drift (PSI / KS test) and emit a metric/alert.
"""
from __future__ import annotations


def check_drift() -> dict:
    raise NotImplementedError("Day 6 (stretch): implement drift detection")
