import unittest
from pathlib import Path

from tests.test_workspace import config_for
from harness.loop_controller import LoopController
from harness.orchestrator import Orchestrator
from harness.schemas.loop_state import LoopState


class LoopControllerTests(unittest.TestCase):
    def test_stops_on_total_iteration_limit(self) -> None:
        config = config_for(Path("/tmp/harness-test"))
        state = LoopState(total_iterations=config.max_total_iterations)
        decision = LoopController(config).stop_reason(state)
        self.assertTrue(decision.should_stop)
        self.assertIn("maximum total iterations", decision.reason)

    def test_allows_under_limits(self) -> None:
        config = config_for(Path("/tmp/harness-test"))
        state = LoopState(total_iterations=0, sprint_iterations=0)
        decision = LoopController(config).stop_reason(state)
        self.assertFalse(decision.should_stop)

    def test_completion_blocked_until_minimum_iterations(self) -> None:
        config = config_for(Path("/tmp/harness-test"))
        config = config.__class__(**{**config.__dict__, "min_iterations_per_sprint": 2})
        orchestrator = Orchestrator(config)
        state = LoopState(sprint_iterations=1)
        self.assertIn("minimum sprint iterations", orchestrator._completion_blocker(state))


if __name__ == "__main__":
    unittest.main()
