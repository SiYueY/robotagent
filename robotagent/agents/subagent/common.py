from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Mapping

from deepagents.middleware.subagents import SubAgent

_JSON_BLOCK = re.compile(r"\{.*\}", re.DOTALL)


def extract_json_object(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    match = _JSON_BLOCK.search(text)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    if isinstance(data, dict):
        return data
    return None


def normalize_text(text: str) -> str:
    return str(text or "").strip().lower()


def pick_first_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def resolve_prompt_path(path: str) -> Path:
    prompt_path = Path(path)
    if prompt_path.is_absolute():
        return prompt_path
    return Path(__file__).resolve().parents[2] / prompt_path


def load_prompt_file(path: str) -> str | None:
    prompt_path = resolve_prompt_path(path)
    if not prompt_path.exists():
        return None
    return prompt_path.read_text(encoding="utf-8").strip()


class _SafeDict(dict):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def format_prompt(text: str, variables: Mapping[str, Any] | None = None) -> str:
    if variables is None:
        return text
    return text.format_map(_SafeDict(**variables))


def build_subagent(name: str, description: str, graph: Any) -> SubAgent:
    try:
        return SubAgent(name=name, description=description, graph=graph)
    except TypeError:
        return SubAgent(name=name, description=description, runnable=graph)
