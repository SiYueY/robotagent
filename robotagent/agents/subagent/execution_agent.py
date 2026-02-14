from __future__ import annotations

from typing import Any, TypedDict

from langchain_core.language_models import BaseChatModel
from langgraph.graph import END, StateGraph

from deepagents.middleware.subagents import SubAgent

from robotagent.agents.subagent.common import (
    build_subagent,
    extract_json_object,
    format_prompt,
    load_prompt_file,
    normalize_text,
    pick_first_str,
)
from robotagent.prompts import build_prompt


class ExecutionState(TypedDict, total=False):
    input: str
    plan: list[str]
    actions: list[str]
    output: str


class ExecutionAgent:
    def __init__(
        self,
        model: BaseChatModel | None = None,
        *,
        prompt_group: str | None = None,
        prompt_path: str | None = None,
    ):
        self.model = model
        self.prompt_group = prompt_group
        self.prompt_path = prompt_path
        self.graph = self._build_graph().compile()

    def _build_graph(self) -> StateGraph:
        graph: StateGraph[ExecutionState] = StateGraph(ExecutionState)
        graph.add_node("plan", self._plan)
        graph.set_entry_point("plan")
        graph.add_edge("plan", END)
        return graph

    def _plan(self, state: ExecutionState) -> ExecutionState:
        text = state.get("input", "")
        plan, actions = self._heuristic_plan(text)
        if self.model is not None:
            model_result = self._model_plan(text)
            if model_result is not None:
                raw_plan = model_result.get("plan", plan)
                raw_actions = model_result.get("actions", actions)
                if isinstance(raw_plan, list):
                    plan = [pick_first_str(item) for item in raw_plan if pick_first_str(item)]
                if isinstance(raw_actions, list):
                    actions = [pick_first_str(item) for item in raw_actions if pick_first_str(item)]
        output = f"plan={plan}; actions={actions}"
        return {**state, "plan": plan, "actions": actions, "output": output}

    def _model_plan(self, text: str) -> dict[str, Any] | None:
        prompt = self._build_prompt(text)
        try:
            response = self.model.invoke(prompt)
        except Exception:
            return None
        return extract_json_object(getattr(response, "content", "") or "")

    def _build_prompt(self, text: str) -> str:
        if self.prompt_path:
            content = load_prompt_file(self.prompt_path)
            if content:
                return format_prompt(content, {"input": text})
        group = self.prompt_group or "execution"
        return build_prompt(group, variables={"input": text})

    @staticmethod
    def _heuristic_plan(text: str) -> tuple[list[str], list[str]]:
        lower = normalize_text(text)
        if any(word in lower for word in ["抓", "取", "拿", "拾取", "pick", "grab"]):
            return (
                ["locate target", "move above target", "close gripper", "lift"],
                ["scan", "approach", "grip", "lift"],
            )
        if any(word in lower for word in ["放", "放置", "放下", "place", "put", "drop"]):
            return (
                ["move to placement", "lower", "open gripper", "retract"],
                ["approach", "lower", "release", "retreat"],
            )
        if any(word in lower for word in ["移动", "去", "move", "go"]):
            return (
                ["plan path", "move along path", "verify pose"],
                ["plan", "move", "check"],
            )
        if any(word in lower for word in ["停止", "急停", "停下", "stop", "halt", "emergency"]):
            return (
                ["halt motion", "set safe state", "confirm stop"],
                ["halt", "safe", "confirm"],
            )
        return (
            ["request clarification"],
            ["ask"],
        )

    def as_subagent(self) -> SubAgent:
        return build_subagent(
            name="execution",
            description="Generate execution plans and low-level actions.",
            graph=self.graph,
        )


def create_execution_subagent(
    model: BaseChatModel | None = None,
    *,
    prompt_group: str | None = None,
    prompt_path: str | None = None,
) -> SubAgent:
    return ExecutionAgent(
        model=model,
        prompt_group=prompt_group,
        prompt_path=prompt_path,
    ).as_subagent()
