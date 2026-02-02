from typing import Any, Literal

from langchain.chat_models import init_chat_model, BaseChatModel


def create_chat_model(
        model: str,
        model_provider: str | None = None,
        configurable_fields: Literal["any"] | list[str] | tuple[str, ...] | None = None,
        config_prefix: str | None = None,
        **kwargs: Any,
) -> BaseChatModel:
    return init_chat_model(
        model=model,
        model_provider=model_provider,
        configurable_fields=configurable_fields,
        config_prefix=config_prefix,
        **kwargs,
    )
