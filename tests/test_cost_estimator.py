import os
import unittest
from unittest.mock import patch

from harness.cost_estimator import estimate_cost_usd


class CostEstimatorTests(unittest.TestCase):
    def test_deepseek_reasoner_default_estimate(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            cost = estimate_cost_usd("deepseek/deepseek-reasoner", 1_000_000, 1_000_000)
        self.assertEqual(cost, 2.8)

    def test_provider_env_override(self) -> None:
        with patch.dict(
            os.environ,
            {
                "COST_MOONSHOT_INPUT_USD_PER_1M": "0.60",
                "COST_MOONSHOT_OUTPUT_USD_PER_1M": "2.50",
            },
            clear=True,
        ):
            cost = estimate_cost_usd("moonshot/kimi-k2.5", 500_000, 100_000)
        self.assertEqual(cost, 0.55)

    def test_model_env_override_wins(self) -> None:
        with patch.dict(
            os.environ,
            {
                "COST_MOONSHOT_INPUT_USD_PER_1M": "99",
                "COST_MOONSHOT_OUTPUT_USD_PER_1M": "99",
                "COST_MOONSHOT_KIMI_K2_5_INPUT_USD_PER_1M": "1",
                "COST_MOONSHOT_KIMI_K2_5_OUTPUT_USD_PER_1M": "3",
            },
            clear=True,
        ):
            cost = estimate_cost_usd("moonshot/kimi-k2.5", 1_000_000, 1_000_000)
        self.assertEqual(cost, 4.0)


if __name__ == "__main__":
    unittest.main()

