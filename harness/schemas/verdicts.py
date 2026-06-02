"""Evaluator verdict constants."""

from enum import StrEnum


class Verdict(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    CRITICAL_ARCHITECTURE_FAILURE = "CRITICAL_ARCHITECTURE_FAILURE"
    ABORT = "ABORT"


class Recommendation(StrEnum):
    CONTINUE = "CONTINUE"
    REBUILD_COMPONENT = "REBUILD_COMPONENT"
    PIVOT_ARCHITECTURE = "PIVOT_ARCHITECTURE"
    ABORT = "ABORT"
