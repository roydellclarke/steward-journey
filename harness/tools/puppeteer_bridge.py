"""Python wrapper around the Node.js Puppeteer bridge."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
from typing import Any


class PuppeteerBridge:
    def __init__(self, script_path: Path | None = None) -> None:
        self.script_path = script_path or Path("puppeteer/evaluator_browser.js").resolve()

    def run(self, action: str, **payload: Any) -> dict[str, Any]:
        command = ["node", str(self.script_path), json.dumps({"action": action, **payload})]
        completed = subprocess.run(command, check=False, capture_output=True, text=True)
        if completed.returncode != 0:
            return {
                "ok": False,
                "action": action,
                "error": completed.stderr.strip() or completed.stdout.strip(),
            }
        try:
            return json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            return {"ok": False, "action": action, "error": f"invalid JSON: {exc}"}

    def navigate(self, url: str) -> dict[str, Any]:
        return self.run("navigate", url=url)

    def click(self, selector: str) -> dict[str, Any]:
        return self.run("click", selector=selector)

    def type(self, selector: str, text: str) -> dict[str, Any]:
        return self.run("type", selector=selector, text=text)

    def screenshot(self, path: str) -> dict[str, Any]:
        return self.run("screenshot", path=path)

    def get_console_errors(self, url: str) -> dict[str, Any]:
        return self.run("get_console_errors", url=url)

    def get_page_text(self, url: str) -> dict[str, Any]:
        return self.run("get_page_text", url=url)

    def wait_for_selector(self, url: str, selector: str) -> dict[str, Any]:
        return self.run("wait_for_selector", url=url, selector=selector)

    def evaluate_dom(self, url: str, script: str) -> dict[str, Any]:
        return self.run("evaluate_dom", url=url, script=script)

    def audit(
        self,
        url: str,
        screenshot_path: str,
        click_selector: str | None = None,
        viewports: list[dict[str, Any]] | None = None,
        screenshot_paths: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        return self.run(
            "audit",
            url=url,
            screenshotPath=screenshot_path,
            clickSelector=click_selector,
            viewports=viewports,
            screenshotPaths=screenshot_paths,
        )
