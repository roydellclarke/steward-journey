"""Preflight checks for the harness runtime."""

from __future__ import annotations

from dataclasses import dataclass, asdict
import os
from pathlib import Path
import shutil
import subprocess

from harness.config import HarnessConfig
from harness.workspace import WORKSPACE_DIRS


@dataclass(frozen=True)
class DoctorCheck:
    name: str
    status: str
    detail: str

    @property
    def ok(self) -> bool:
        return self.status == "PASS"


class Doctor:
    def __init__(self, config: HarnessConfig) -> None:
        self.config = config

    def run(self) -> list[DoctorCheck]:
        checks = [
            self._workspace_writable(),
            self._workspace_dirs(),
            self._python_available(),
            self._node_available(),
            self._puppeteer_bridge_present(),
            self._puppeteer_package_installed(),
            self._env_file_present(),
            self._model_routes_configured(),
            self._llm_keys_when_enabled(),
            self._security_policy_present(),
        ]
        return checks

    def as_jsonable(self) -> list[dict[str, str]]:
        return [asdict(check) for check in self.run()]

    def _workspace_writable(self) -> DoctorCheck:
        try:
            self.config.workspace_root.mkdir(parents=True, exist_ok=True)
            probe = self.config.workspace_root / ".write_probe"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            return DoctorCheck("workspace_writable", "PASS", str(self.config.workspace_root))
        except OSError as exc:
            return DoctorCheck("workspace_writable", "FAIL", str(exc))

    def _workspace_dirs(self) -> DoctorCheck:
        missing = [directory for directory in WORKSPACE_DIRS if not (self.config.workspace_root / directory).exists()]
        if missing:
            return DoctorCheck("workspace_directories", "WARN", "missing before init: " + ", ".join(missing))
        return DoctorCheck("workspace_directories", "PASS", "all required directories exist")

    def _python_available(self) -> DoctorCheck:
        python_bin = os.getenv("HARNESS_PYTHON", "python3")
        resolved = shutil.which(python_bin) or python_bin
        try:
            completed = subprocess.run([resolved, "--version"], capture_output=True, text=True, check=False)
        except OSError as exc:
            return DoctorCheck("python", "FAIL", f"{resolved}: {exc}")
        status = "PASS" if completed.returncode == 0 else "FAIL"
        return DoctorCheck("python", status, (completed.stdout or completed.stderr).strip())

    def _node_available(self) -> DoctorCheck:
        node = shutil.which("node")
        if not node:
            return DoctorCheck("node", "FAIL", "node not found")
        completed = subprocess.run([node, "--version"], capture_output=True, text=True, check=False)
        return DoctorCheck("node", "PASS" if completed.returncode == 0 else "FAIL", completed.stdout.strip())

    def _puppeteer_bridge_present(self) -> DoctorCheck:
        path = Path("puppeteer/evaluator_browser.js")
        return DoctorCheck(
            "puppeteer_bridge",
            "PASS" if path.exists() else "FAIL",
            str(path),
        )

    def _puppeteer_package_installed(self) -> DoctorCheck:
        path = Path("puppeteer/node_modules/puppeteer")
        return DoctorCheck(
            "puppeteer_package",
            "PASS" if path.exists() else "FAIL",
            "run `npm run puppeteer:install`" if not path.exists() else str(path),
        )

    def _env_file_present(self) -> DoctorCheck:
        return DoctorCheck(".env", "PASS" if Path(".env").exists() else "WARN", ".env present" if Path(".env").exists() else "copy .env.example to .env")

    def _model_routes_configured(self) -> DoctorCheck:
        models = [self.config.planner.model, self.config.generator.model, self.config.evaluator.model]
        if all(models):
            return DoctorCheck("model_routes", "PASS", "planner/generator/evaluator model routes configured")
        return DoctorCheck("model_routes", "FAIL", "missing model route")

    def _llm_keys_when_enabled(self) -> DoctorCheck:
        if not self.config.use_llm:
            return DoctorCheck("llm_keys", "PASS", "HARNESS_USE_LLM=false")
        required = []
        routes = [self.config.planner.model, self.config.generator.model, self.config.evaluator.model]
        if any(route.startswith("deepseek/") for route in routes):
            required.append("DEEPSEEK_API_KEY")
        if any(route.startswith(("moonshot/", "kimi/")) for route in routes):
            required.append("MOONSHOT_API_KEY")
        missing = [name for name in required if not os.getenv(name)]
        if missing:
            return DoctorCheck("llm_keys", "FAIL", "missing: " + ", ".join(missing))
        return DoctorCheck("llm_keys", "PASS", "required provider keys are present")

    def _security_policy_present(self) -> DoctorCheck:
        redaction = self.config.workspace_root / "state" / "redaction_policy.md"
        trust = self.config.workspace_root / "state" / "trust_labels.json"
        if redaction.exists() and trust.exists():
            return DoctorCheck("security_policy", "PASS", "redaction policy and trust labels present")
        return DoctorCheck("security_policy", "WARN", "run init to create redaction policy and trust labels")
