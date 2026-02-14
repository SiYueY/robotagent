from typing import Any, Literal, TypeAlias

from langchain.chat_models import init_chat_model
from langchain.chat_models import BaseChatModel as ChatModel

def create_chat_model(
    model: str | None = None,
    model_provider: str | None = None,
    configurable_fields: Literal["any"] | list[str] | tuple[str, ...] | None = None,
    config_prefix: str | None = None,
    **kwargs: Any,
) -> ChatModel:
    if model is None or model_provider is None:
        try:
            from robotagent.configs.settings import get_settings

            settings = get_settings()
            if model is None:
                model = settings.llm.model
            if model_provider is None:
                model_provider = settings.llm.provider
            if "temperature" not in kwargs:
                kwargs["temperature"] = settings.llm.temperature
            if "max_tokens" not in kwargs and settings.llm.max_tokens:
                kwargs["max_tokens"] = settings.llm.max_tokens
            if "api_key" not in kwargs and settings.llm.api_key:
                kwargs["api_key"] = settings.llm.api_key
            provider_cfg = settings.llm.providers.get(model_provider or "")
            if provider_cfg:
                if "api_key" not in kwargs and provider_cfg.api_key:
                    kwargs["api_key"] = provider_cfg.api_key
                if "base_url" not in kwargs and provider_cfg.base_url:
                    kwargs["base_url"] = provider_cfg.base_url
                if "organization" not in kwargs and provider_cfg.organization:
                    kwargs["organization"] = provider_cfg.organization
        except Exception:
            pass
    if model is None:
        raise ValueError("model must be provided or configured via settings")
    return init_chat_model(
        model=model,
        model_provider=model_provider,
        configurable_fields=configurable_fields,
        config_prefix=config_prefix,
        **kwargs,
    )

