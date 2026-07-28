"""Yes/no answers must move the readiness score in the right direction, whether
the client sends a real boolean or a string. A "yes" to documenting your SOPs
must raise the score, never be silently ignored. Pure logic, no web stack.

Run: python -m unittest discover -s backend/tests
"""

from __future__ import annotations

import unittest

from app.services.scoring import score_intake
from app.storage.intake_state import merge_intake_patch, migrate_profile_to_intake_state


def _score_with_sops(value):
    state = migrate_profile_to_intake_state(None, {})
    if value is not None:
        state = merge_intake_patch(
            state, {"processDocumentation": {"sopsExist": {"value": value, "status": "answered"}}}
        )
    result = score_intake(state)
    return result["overall"], result["dimensions"]["process_documentation"]


class SopsScoringTests(unittest.TestCase):
    def test_yes_raises_score_regardless_of_encoding(self):
        base_overall, base_dim = _score_with_sops(None)  # unanswered baseline
        for encoding in (True, "true", "yes", "Yes", 1):
            overall, dim = _score_with_sops(encoding)
            self.assertGreater(dim, base_dim, f"sops={encoding!r} should raise the driver")
            self.assertGreater(overall, base_overall, f"sops={encoding!r} should raise the overall")

    def test_no_lowers_score_regardless_of_encoding(self):
        base_overall, base_dim = _score_with_sops(None)
        for encoding in (False, "false", "no", "No", 0):
            overall, dim = _score_with_sops(encoding)
            self.assertLess(dim, base_dim, f"sops={encoding!r} should lower the driver")

    def test_unknown_is_neutral(self):
        base_overall, base_dim = _score_with_sops(None)
        self.assertEqual(base_dim, 2.5)


def _score_with_areas(areas):
    state = migrate_profile_to_intake_state(None, {})
    if areas is not None:
        state = merge_intake_patch(
            state, {"processDocumentation": {"documentedAreas": {"value": areas, "status": "answered"}}}
        )
    result = score_intake(state)
    return result["dimensions"]["process_documentation"]


class DocumentedAreasScoringTests(unittest.TestCase):
    ALL = ["operations", "sales", "finance", "customer handoff", "hr", "safety"]

    def test_every_area_helps_and_more_is_monotonic(self):
        # Documenting any area must raise the driver, and documenting more must
        # never lower it. This was the bug: 1-2 areas earned nothing.
        none = _score_with_areas([])
        one = _score_with_areas(self.ALL[:1])
        three = _score_with_areas(self.ALL[:3])
        six = _score_with_areas(self.ALL)
        self.assertGreater(one, none)
        self.assertGreaterEqual(three, one)
        self.assertGreaterEqual(six, three)

    def test_comma_string_is_counted(self):
        self.assertGreater(_score_with_areas("operations, sales, finance"), _score_with_areas([]))


if __name__ == "__main__":
    unittest.main()
