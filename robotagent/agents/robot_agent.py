from pathlib import Path

from langchain_core.language_models import BaseChatModel

from deepagents import create_deep_agent
from robotagent.agents.subagent import (
    create_execution_subagent,
    create_intent_subagent,
    create_perception_subagent,
)
from robotagent.configs.settings import AgentConfig, LLMOverrideSettings, get_settings
from robotagent.models.chat_model import create_chat_model
from robotagent.prompts import build_prompt

class RobotAgent:
    def _override_is_empty(self, override: LLMOverrideSettings | None) -> bool:
        if override is None:
            return True
        return all(
            value is None
            for value in (
                override.provider,
                override.model,
                override.temperature,
                override.max_tokens,
                override.api_key,
                override.base_url,
                override.organization,
            )
        )

    def _build_model_from_override(self, override: LLMOverrideSettings) -> BaseChatModel:
        kwargs: dict[str, object] = {}
        if override.temperature is not None:
            kwargs["temperature"] = override.temperature
        if override.max_tokens is not None:
            kwargs["max_tokens"] = override.max_tokens
        if override.api_key is not None:
            kwargs["api_key"] = override.api_key
        if override.base_url is not None:
            kwargs["base_url"] = override.base_url
        if override.organization is not None:
            kwargs["organization"] = override.organization
        if override.provider:
            try:
                from robotagent.configs.settings import get_settings

                settings = get_settings()
                provider_cfg = settings.llm.providers.get(override.provider)
                if provider_cfg:
                    if "api_key" not in kwargs and provider_cfg.api_key:
                        kwargs["api_key"] = provider_cfg.api_key
                    if "base_url" not in kwargs and provider_cfg.base_url:
                        kwargs["base_url"] = provider_cfg.base_url
                    if "organization" not in kwargs and provider_cfg.organization:
                        kwargs["organization"] = provider_cfg.organization
            except Exception:
                pass
        return create_chat_model(
            model=override.model,
            model_provider=override.provider,
            **kwargs,
        )

    def __init__(
        self,
        model: str | BaseChatModel | None = None,
        *,
        model_path: str | None = None,
        **kwargs,
    ):
        settings = get_settings()
        agents = settings.agents
        main_config = agents.get("robot-agent") or agents.get("robot_agent") or AgentConfig()

        base_model: BaseChatModel
        if isinstance(model, BaseChatModel):
            base_model = model
        else:
            model_name = model or model_path
            if model_name is not None:
                base_model = create_chat_model(model_name)
            elif not self._override_is_empty(main_config.model):
                base_model = self._build_model_from_override(main_config.model)
            else:
                base_model = create_chat_model(None)

        def subagent_model(name: str) -> BaseChatModel:
            override = agents.get(name)
            if override is None or self._override_is_empty(override.model):
                return base_model
            return self._build_model_from_override(override.model)

        def subagent_prompt(name: str) -> tuple[str | None, str | None]:
            override = agents.get(name)
            if override is None:
                return name, None
            prompt_group = override.prompt_group or override.system_prompt_group or name
            prompt_path = override.prompt_path or override.system_prompt_path
            return prompt_group, prompt_path

        intent_group, intent_path = subagent_prompt("intent")
        perception_group, perception_path = subagent_prompt("perception")
        execution_group, execution_path = subagent_prompt("execution")

        subagents = [
            create_intent_subagent(
                subagent_model("intent"),
                prompt_group=intent_group,
                prompt_path=intent_path,
            ),
            create_perception_subagent(
                subagent_model("perception"),
                prompt_group=perception_group,
                prompt_path=perception_path,
            ),
            create_execution_subagent(
                subagent_model("execution"),
                prompt_group=execution_group,
                prompt_path=execution_path,
            ),
        ]
        system_prompt = kwargs.pop("system_prompt", None)
        if system_prompt is None:
            prompt_path = main_config.prompt_path or main_config.system_prompt_path
            if prompt_path:
                path = Path(prompt_path)
                if not path.is_absolute():
                    path = Path(__file__).resolve().parents[2] / path
                if path.exists():
                    system_prompt = path.read_text(encoding="utf-8").strip()
            prompt_group = main_config.prompt_group or main_config.system_prompt_group
            if system_prompt is None and prompt_group:
                system_prompt = build_prompt(prompt_group)
            if system_prompt is None:
                system_prompt = (
                    "You are a robot control agent. Use subagents for intent, perception, and execution planning."
                )
        self.deep_agent = create_deep_agent(
            model=base_model,
            subagents=subagents,
            system_prompt=system_prompt,
            **kwargs,
        )

    def __call__(self, text: str) -> str:
        return self.deep_agent(text)
