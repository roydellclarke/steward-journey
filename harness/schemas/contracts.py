"""Contract parsing helpers."""

from __future__ import annotations

import re


def extract_startup_command(contract: str) -> str | None:
    match = re.search(r"## App Startup Command\s+```(?:bash)?\s*(.*?)```", contract, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def extract_routes(contract: str) -> list[str]:
    routes: list[str] = []
    in_routes = False
    for line in contract.splitlines():
        if line.startswith("## Routes"):
            in_routes = True
            continue
        if in_routes and line.startswith("## "):
            break
        if in_routes and line.strip().startswith("-"):
            routes.append(line.strip().lstrip("- ").strip())
    return routes
