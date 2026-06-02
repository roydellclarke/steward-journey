import unittest

from mvp.stewardpath.backend.reasoning import OwnerProfile, analyze_owner_profile


class StewardPathReasoningTests(unittest.TestCase):
    def profile(self, **overrides):
        data = {
            "business_name": "Harbor Tool & Die",
            "industry": "specialty manufacturing",
            "years_operating": 34,
            "employees": 28,
            "revenue_range": "$5M-$10M",
            "profit_margin": "12-15%",
            "owner_dependency": "medium - owner owns key customer relationships",
            "timeline": "2-4 years",
            "owner_goal": "step back while protecting employees",
            "fears": "a buyer will cut staff",
            "non_negotiables": "keep the local team",
            "family_context": "children do not want to operate the company",
            "next_owner_traits": "patient operator with local credibility",
        }
        data.update(overrides)
        return OwnerProfile(**data)

    def test_analysis_contains_required_mvp_sections(self) -> None:
        analysis = analyze_owner_profile(self.profile())
        for key in [
            "jtbd",
            "growth_discovery",
            "buffett_quality",
            "readiness",
            "buyer_paths",
            "roadmap",
            "narratives",
            "disclaimers",
        ]:
            self.assertIn(key, analysis)

    def test_low_founder_dependency_improves_readiness(self) -> None:
        high = analyze_owner_profile(self.profile(owner_dependency="high - everything depends on me"))
        low = analyze_owner_profile(self.profile(owner_dependency="low - team runs daily operations"))
        self.assertGreater(low["readiness"]["overall"], high["readiness"]["overall"])

    def test_growth_discovery_has_north_star_and_rate_limit(self) -> None:
        analysis = analyze_owner_profile(self.profile())
        growth = analysis["growth_discovery"]
        self.assertIn("you", growth["north_star_metric"].lower())
        self.assertIn("protected", growth["north_star_metric"].lower())
        self.assertIn("lost", growth["rate_limiting_step_hypothesis"])
        self.assertGreaterEqual(len(growth["growth_levers"]), 3)

    def test_disclaimers_prevent_advice_confusion(self) -> None:
        analysis = analyze_owner_profile(self.profile())
        disclaimer_text = " ".join(analysis["disclaimers"])
        self.assertIn("Not legal", disclaimer_text)
        self.assertIn("Not a formal valuation", disclaimer_text)


if __name__ == "__main__":
    unittest.main()
