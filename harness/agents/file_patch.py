"""Parse safe file blocks from live Generator model output."""

from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class GeneratedFile:
    path: str
    content: str


FILE_BLOCK_RE = re.compile(
    r"```file[: ](?P<path>[^\n]+)\n(?P<content>.*?)```",
    re.DOTALL,
)


def extract_generated_files(response: str) -> list[GeneratedFile]:
    files: list[GeneratedFile] = []
    for match in FILE_BLOCK_RE.finditer(response):
        raw_path = match.group("path").strip()
        path = normalize_generated_path(raw_path)
        files.append(GeneratedFile(path=path, content=match.group("content").rstrip() + "\n"))
    return files


def normalize_generated_path(raw_path: str) -> str:
    path = raw_path.removeprefix("/workspace/").lstrip("/")
    if path.startswith("../") or "/../" in path or path == "..":
        raise ValueError(f"generated file path escapes workspace: {raw_path}")
    if not path.startswith("src/"):
        raise ValueError(f"generated file path must be under src/: {raw_path}")
    return path
