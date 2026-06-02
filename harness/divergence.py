"""Evaluator divergence scoring."""

from __future__ import annotations

from pathlib import Path


class DivergenceScorer:
    def __init__(self, workspace_root: Path) -> None:
        self.path = workspace_root / "state" / "divergence_log.md"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def score_report(self, report: str) -> float:
        warnings: list[tuple[str, float]] = []
        normalized = report.lower()
        if "## puppeteer actions performed" not in normalized:
            warnings.append(("missing Puppeteer section", 0.25))
        if "looks good" in normalized or "great job" in normalized:
            warnings.append(("vague praise", 0.2))
        if "| criterion | result | evidence | notes |" not in normalized:
            warnings.append(("missing criteria table", 0.25))
        if "pass" in normalized and "screenshot" not in normalized:
            warnings.append(("pass without screenshot evidence", 0.2))
        score = min(sum(weight for _label, weight in warnings), 1.0)
        self.path.write_text(
            "# Divergence Log\n\n"
            f"## Latest Score\n\n{score}\n\n"
            "## Warnings\n\n"
            + "\n".join(f"- {label}: {weight}" for label, weight in warnings)
            + ("\n" if warnings else "- None\n"),
            encoding="utf-8",
        )
        return score
