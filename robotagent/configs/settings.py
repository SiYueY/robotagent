from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SystemSettings(BaseModel):
    env: Literal["dev", "test", "prod"] = "dev"
    log_level: str = "INFO"


class LLMProviderSettings(BaseModel):
    api_key: str | None = None
    base_url: str | None = None
    organization: str | None = None


class LLMSettings(BaseModel):
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    temperature: float = 0.2
    max_tokens: int = 1024
    api_key: str | None = None
    providers: dict[str, LLMProviderSettings] = Field(default_factory=dict)


class LLMOverrideSettings(BaseModel):
    provider: str | None = None
    model: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    api_key: str | None = None
    base_url: str | None = None
    organization: str | None = None


class AgentConfig(BaseModel):
    system_prompt_group: str | None = None
    system_prompt_path: str | None = None
    prompt_group: str | None = None
    prompt_path: str | None = None
    use_skills: bool = True
    use_memory: bool = True
    model: LLMOverrideSettings = Field(default_factory=LLMOverrideSettings)


class PromptSettings(BaseModel):
    root: str = "robotagent/prompts"
    index_file: str = "robotagent/prompts/prompt_index.yaml"
    langfuse_enabled: bool = True


class LangfuseSettings(BaseModel):
    public_key: str | None = None
    secret_key: str | None = None
    base_url: str | None = None
    label: str = "production"


class StorageSettings(BaseModel):
    vector_store: str = "milvus"
    milvus_uri: str | None = None


class ConfigFileSettings(BaseModel):
    files: list[str] = []
    system: str | None = None
    llm: str | None = None
    agents: str | None = None
    prompt: str | None = None
    langfuse: str | None = None
    storage: str | None = None


class AppSettings(BaseSettings):
    system: SystemSettings = SystemSettings()
    llm: LLMSettings = LLMSettings()
    agents: dict[str, AgentConfig] = Field(default_factory=dict)
    prompt: PromptSettings = PromptSettings()
    langfuse: LangfuseSettings = LangfuseSettings()
    storage: StorageSettings = StorageSettings()
    config: ConfigFileSettings = ConfigFileSettings()

    model_config = SettingsConfigDict(
        env_prefix="",
        env_nested_delimiter="_",
        env_file=".env",
        case_sensitive=False,
    )


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_path(path: str | Path) -> Path:
    path = Path(path)
    if path.is_absolute():
        return path
    return _repo_root() / path


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except Exception:
        return {}
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _apply_section(settings: AppSettings, name: str, data: dict[str, Any]) -> AppSettings:
    if not data:
        return settings
    current = getattr(settings, name)
    updated = current.model_copy(update=data)
    return settings.model_copy(update={name: updated})


def _apply_agents(settings: AppSettings, data: dict[str, Any]) -> AppSettings:
    if not data:
        return settings
    current = dict(settings.agents)
    for name, value in data.items():
        if not isinstance(value, dict):
            continue
        existing = current.get(name, AgentConfig())
        current[name] = existing.model_copy(update=value)
    return settings.model_copy(update={"agents": current})


def _merge_from_mapping(settings: AppSettings, data: dict[str, Any]) -> AppSettings:
    for section in ("system", "llm", "prompt", "langfuse", "storage"):
        value = data.get(section)
        if isinstance(value, dict):
            settings = _apply_section(settings, section, value)
    agents = data.get("agents")
    if isinstance(agents, dict):
        settings = _apply_agents(settings, agents)
    return settings


def _merge_from_file(settings: AppSettings, path: str | Path, section: str | None = None) -> AppSettings:
    data = _load_yaml(_resolve_path(path))
    if not data:
        return settings
    if section is None:
        return _merge_from_mapping(settings, data)
    if section == "agents":
        if section in data and isinstance(data[section], dict):
            return _apply_agents(settings, data[section])
        if isinstance(data, dict):
            return _apply_agents(settings, data)
        return settings
    if section in data and isinstance(data[section], dict):
        return _apply_section(settings, section, data[section])
    if isinstance(data, dict):
        return _apply_section(settings, section, data)
    return settings


def _parse_int(value: str) -> int | None:
    try:
        return int(value)
    except ValueError:
        return None


def _parse_float(value: str) -> float | None:
    try:
        return float(value)
    except ValueError:
        return None


def _apply_env_overrides(settings: AppSettings) -> AppSettings:
    llm_updates: dict[str, Any] = {}
    env = os.getenv("LLM_PROVIDER")
    if env:
        llm_updates["provider"] = env
    env = os.getenv("LLM_MODEL")
    if env:
        llm_updates["model"] = env
    env = os.getenv("LLM_TEMPERATURE")
    if env:
        value = _parse_float(env)
        if value is not None:
            llm_updates["temperature"] = value
    env = os.getenv("LLM_MAX_TOKENS")
    if env:
        value = _parse_int(env)
        if value is not None:
            llm_updates["max_tokens"] = value
    env = os.getenv("LLM_API_KEY")
    if env:
        llm_updates["api_key"] = env

    provider_overrides: dict[str, dict[str, Any]] = {}
    for key, value in os.environ.items():
        if not key.startswith("LLM_PROVIDERS_"):
            continue
        remainder = key[len("LLM_PROVIDERS_") :]
        if "_" not in remainder:
            continue
        provider_raw, field_raw = remainder.split("_", 1)
        provider = provider_raw.lower()
        field = field_raw.lower()
        if field not in {"api_key", "base_url", "organization"}:
            continue
        provider_overrides.setdefault(provider, {})[field] = value

    if llm_updates or provider_overrides:
        providers = dict(settings.llm.providers)
        for provider, data in provider_overrides.items():
            current = providers.get(provider, LLMProviderSettings())
            providers[provider] = current.model_copy(update=data)
        if providers:
            llm_updates["providers"] = providers
        updated_llm = settings.llm.model_copy(update=llm_updates)
        settings = settings.model_copy(update={"llm": updated_llm})

    langfuse_updates: dict[str, Any] = {}
    env = os.getenv("LANGFUSE_PUBLIC_KEY")
    if env:
        langfuse_updates["public_key"] = env
    env = os.getenv("LANGFUSE_SECRET_KEY")
    if env:
        langfuse_updates["secret_key"] = env
    env = os.getenv("LANGFUSE_BASE_URL")
    if env:
        langfuse_updates["base_url"] = env
    env = os.getenv("LANGFUSE_LABEL")
    if env:
        langfuse_updates["label"] = env
    if langfuse_updates:
        updated_langfuse = settings.langfuse.model_copy(update=langfuse_updates)
        settings = settings.model_copy(update={"langfuse": updated_langfuse})

    return settings


def _apply_file_overrides(settings: AppSettings) -> AppSettings:
    for path in settings.config.files:
        settings = _merge_from_file(settings, path)
    if settings.config.system:
        settings = _merge_from_file(settings, settings.config.system, "system")
    if settings.config.llm:
        settings = _merge_from_file(settings, settings.config.llm, "llm")
    if settings.config.agents:
        settings = _merge_from_file(settings, settings.config.agents, "agents")
    if settings.config.prompt:
        settings = _merge_from_file(settings, settings.config.prompt, "prompt")
    if settings.config.langfuse:
        settings = _merge_from_file(settings, settings.config.langfuse, "langfuse")
    if settings.config.storage:
        settings = _merge_from_file(settings, settings.config.storage, "storage")
    return settings


@lru_cache
def get_settings() -> AppSettings:
    settings = AppSettings()
    settings = _apply_file_overrides(settings)
    return _apply_env_overrides(settings)
