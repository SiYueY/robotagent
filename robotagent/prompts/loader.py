from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

try:
    import yaml
except Exception:  # pragma: no cover - optional dependency
    yaml = None


_INDEX_FILE = "prompt_index.yaml"
_DEFAULT_SECTIONS = ("system", "task", "output", "examples")
_SINGLE_FILE_KEY = "prompt"
from robotagent.prompts.langfuse_prompt_manager import render_langfuse_prompt


class _SafeDict(dict):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _index_path() -> Path:
    try:
        from robotagent.configs.settings import get_settings

        settings = get_settings()
        if settings.prompt.index_file:
            path = Path(settings.prompt.index_file)
            if path.is_absolute():
                return path
            return _repo_root() / path
    except Exception:
        pass
    return _repo_root() / "robotagent" / "prompts" / _INDEX_FILE


def _load_index() -> dict[str, Any]:
    path = _index_path()
    if not path.exists() or yaml is None:
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        return data
    return {}




def _prompt_root() -> Path:
    try:
        from robotagent.configs.settings import get_settings

        settings = get_settings()
        if settings.prompt.root:
            path = Path(settings.prompt.root)
            if path.is_absolute():
                return path
            return _repo_root() / path
    except Exception:
        pass
    return _repo_root() / "robotagent" / "prompts"


def prompt_path(group: str, section: str) -> Path:
    index = _load_index()
    root = _prompt_root()
    index_root = index.get("root") if isinstance(index, dict) else None
    if isinstance(index_root, str):
        root = _repo_root() / index_root
    prompts = index.get("prompts", {}) if isinstance(index, dict) else {}
    group_map = prompts.get(group, {}) if isinstance(prompts, dict) else {}
    rel = None
    if isinstance(group_map, Mapping):
        rel = group_map.get(section)
    if isinstance(rel, str):
        rel_path = Path(rel)
        if rel_path.is_absolute():
            return rel_path
        return root / rel_path
    return root / group / f"{section}.md"


def load_prompt(group: str, section: str, *, default: str = "") -> str:
    path = prompt_path(group, section)
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    return default.strip()


def _read_local_group(group: str) -> str:
    index = _load_index()
    prompts = index.get("prompts", {}) if isinstance(index, dict) else {}
    group_map = prompts.get(group, {}) if isinstance(prompts, dict) else {}
    single = None
    if isinstance(group_map, Mapping):
        single = group_map.get(_SINGLE_FILE_KEY)
    if isinstance(single, str):
        path = prompt_path(group, _SINGLE_FILE_KEY)
        if path.exists():
            return path.read_text(encoding="utf-8").strip()
    parts: list[str] = []
    for section in _DEFAULT_SECTIONS:
        text = load_prompt(group, section)
        if text:
            parts.append(text)
    return "\n\n".join(parts)


def build_prompt(group: str, *, variables: Mapping[str, Any] | None = None) -> str:
    rendered = render_langfuse_prompt(group, variables=variables)
    if rendered:
        return rendered
    joined = _read_local_group(group)
    if not variables:
        return joined
    return joined.format_map(_SafeDict(**variables))
