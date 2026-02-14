from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping

import yaml

_DEFAULT_SECTIONS = ("system", "task", "output", "examples")
_SINGLE_FILE_KEY = "prompt"
_VAR_TOKEN = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _index_path() -> Path:
    settings = _settings()
    if settings is not None and settings.prompt.index_file:
        path = Path(settings.prompt.index_file)
        if path.is_absolute():
            return path
        return _repo_root() / path
    return _repo_root() / "robotagent" / "prompts" / "prompt_index.yaml"


def load_index() -> dict[str, Any]:
    path = _index_path()
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        return data
    return {}


def _prompt_root(index: Mapping[str, Any]) -> Path:
    settings = _settings()
    if settings is not None and settings.prompt.root:
        path = Path(settings.prompt.root)
        if path.is_absolute():
            return path
        return _repo_root() / path
    root_value = index.get("root")
    if isinstance(root_value, str):
        return _repo_root() / root_value
    return _repo_root() / "robotagent" / "prompts"


def _resolve_prompt_path(root: Path, group: str, mapping: Mapping[str, Any], section: str) -> Path:
    rel = mapping.get(section)
    if isinstance(rel, str):
        rel_path = Path(rel)
        if rel_path.is_absolute():
            return rel_path
        return root / rel_path
    return root / group / f"{section}.md"


def _build_local_prompt(root: Path, group: str, mapping: Mapping[str, Any]) -> str:
    single = mapping.get(_SINGLE_FILE_KEY)
    if isinstance(single, str):
        single_path = _resolve_prompt_path(root, group, mapping, _SINGLE_FILE_KEY)
        if single_path.exists():
            return single_path.read_text(encoding="utf-8").strip()
    parts: list[str] = []
    for section in _DEFAULT_SECTIONS:
        path = _resolve_prompt_path(root, group, mapping, section)
        if path.exists():
            content = path.read_text(encoding="utf-8").strip()
            if content:
                parts.append(content)
    return "\n\n".join(parts)


def _to_langfuse_template(text: str) -> str:
    if not text:
        return text
    return _VAR_TOKEN.sub(r"{{\1}}", text)


def _settings():
    try:
        from robotagent.configs.settings import get_settings

        return get_settings()
    except Exception:
        return None


def _is_langfuse_enabled() -> bool:
    settings = _settings()
    if settings is None:
        return False
    if not settings.prompt.langfuse_enabled:
        return False
    return bool(settings.langfuse.public_key and settings.langfuse.secret_key)


@lru_cache(maxsize=1)
def _langfuse_client() -> Any | None:
    if not _is_langfuse_enabled():
        return None
    settings = _settings()
    try:
        from langfuse import Langfuse, get_client  # type: ignore
    except Exception:
        return None

    if settings is not None:
        base_url = settings.langfuse.base_url
        public_key = settings.langfuse.public_key
        secret_key = settings.langfuse.secret_key
        if public_key and secret_key:
            if base_url:
                return Langfuse(
                    public_key=public_key,
                    secret_key=secret_key,
                    base_url=base_url,
                )
            return Langfuse(public_key=public_key, secret_key=secret_key)

    try:
        return get_client()
    except Exception:
        return None


def _groups_from_index(index: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    prompts = index.get("prompts", {}) if isinstance(index, dict) else {}
    if not isinstance(prompts, dict):
        return {}
    return {k: v for k, v in prompts.items() if isinstance(v, Mapping)}


def list_groups() -> list[str]:
    index = load_index()
    return sorted(_groups_from_index(index).keys())


def langfuse_spec(group: str) -> Mapping[str, Any]:
    index = load_index()
    group_map = _groups_from_index(index).get(group, {})
    spec = group_map.get("langfuse") if isinstance(group_map, Mapping) else {}
    return spec if isinstance(spec, Mapping) else {}


def render_langfuse_prompt(group: str, *, variables: Mapping[str, Any] | None = None) -> str | None:
    client = _langfuse_client()
    if client is None:
        return None

    index = load_index()
    groups = _groups_from_index(index)
    group_map = groups.get(group, {})
    spec = group_map.get("langfuse") if isinstance(group_map, Mapping) else {}
    if not isinstance(spec, Mapping):
        return None

    name = spec.get("name") or group
    if not isinstance(name, str) or not name:
        return None

    kwargs: dict[str, Any] = {"name": name}
    for key in ("label", "version", "type", "cache_ttl_seconds"):
        if key in spec:
            kwargs[key] = spec[key]
    if "label" not in kwargs:
        settings = _settings()
        if settings is not None:
            kwargs["label"] = settings.langfuse.label

    fallback = None
    root = _prompt_root(index)
    fallback_group = spec.get("fallback_group") or group
    if isinstance(fallback_group, str):
        fallback_map = groups.get(fallback_group, group_map)
        fallback = _build_local_prompt(root, fallback_group, fallback_map)
    if fallback:
        kwargs.setdefault("fallback", _to_langfuse_template(fallback))

    try:
        prompt_client = client.get_prompt(**kwargs)
        compiled = prompt_client.compile(variables or {})
    except Exception:
        return None

    if isinstance(compiled, list):
        return "\n\n".join(
            f"{item.get('role', 'user')}: {item.get('content', '')}".strip()
            for item in compiled
            if isinstance(item, dict)
        ).strip()
    if isinstance(compiled, str):
        return compiled.strip()
    return None


def upload_prompt_group(
    group: str,
    *,
    label: str | None = None,
    prompt_type: str | None = None,
    name: str | None = None,
    dry_run: bool = False,
) -> str | None:
    client = _langfuse_client()
    if client is None:
        raise RuntimeError("Langfuse client is not available. Check env vars and dependencies.")

    index = load_index()
    groups = _groups_from_index(index)
    if group not in groups:
        raise KeyError(f"Unknown prompt group: {group}")

    group_map = groups[group]
    spec = group_map.get("langfuse") if isinstance(group_map, Mapping) else {}
    if not isinstance(spec, Mapping):
        spec = {}

    root = _prompt_root(index)
    prompt_text = _build_local_prompt(root, group, group_map)
    if not prompt_text:
        raise ValueError(f"Prompt group '{group}' has no content to upload")

    resolved_name = name or spec.get("name") or group
    settings = _settings()
    default_label = settings.langfuse.label if settings is not None else "production"
    resolved_label = label or spec.get("label") or default_label
    resolved_type = prompt_type or spec.get("type") or "text"
    rendered = _to_langfuse_template(prompt_text)

    if dry_run:
        return f"[dry-run] {group} -> name={resolved_name} label={resolved_label} type={resolved_type}"

    client.create_prompt(
        name=resolved_name,
        type=resolved_type,
        prompt=rendered,
        labels=[resolved_label],
    )
    return f"[ok] uploaded {group} -> {resolved_name} ({resolved_label})"


def export_prompt_group(
    group: str,
    *,
    variables: Mapping[str, Any] | None = None,
    output_path: Path | None = None,
) -> Path:
    rendered = render_langfuse_prompt(group, variables=variables)
    if rendered is None:
        raise RuntimeError("Failed to render prompt from Langfuse")

    if output_path is None:
        output_path = _repo_root() / "robotagent" / "prompts" / group / "langfuse.md"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered.strip() + "\n", encoding="utf-8")
    return output_path
