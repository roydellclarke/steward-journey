import unittest
from pathlib import Path

from tests.test_workspace import config_for
from harness.loop_controller import LoopController
from harness.schemas.loop_state import LoopState


class AbortConditionTests(unittest.TestCase):
    def test_stops_on_repeated_failures(self) -> None:
        config = config_for(Path("/tmp/harness-test"))
        state = LoopState(repeated_failure_count=config.max_repeated_failure_count)
        decision = LoopController(config).stop_reason(state)
        self.assertTrue(decision.should_stop)
        self.assertIn("repeated failure", decision.reason)

    def test_stops_on_divergence(self) -> None:
        config = config_for(Path("/tmp/harness-test"))
        state = LoopState(divergence_score=config.divergence_score_threshold)
        decision = LoopController(config).stop_reason(state)
        self.assertTrue(decision.should_stop)
        self.assertIn("divergence", decision.reason)


if __name__ == "__main__":
    unittest.main()
