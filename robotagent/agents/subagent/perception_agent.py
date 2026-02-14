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


class PerceptionState(TypedDict, total=False):
    input: str
    objects: list[str]
    scene: str
    output: str


class PerceptionAgent:
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
        graph: StateGraph[PerceptionState] = StateGraph(PerceptionState)
        graph.add_node("perceive", self._perceive)
        graph.set_entry_point("perceive")
        graph.add_edge("perceive", END)
        return graph

    def _perceive(self, state: PerceptionState) -> PerceptionState:
        text = state.get("input", "")
        objects, scene = self._heuristic_perception(text)
        if self.model is not None:
            model_result = self._model_perception(text)
            if model_result is not None:
                raw_objects = model_result.get("objects", objects)
                if isinstance(raw_objects, list):
                    objects = [pick_first_str(item) for item in raw_objects if pick_first_str(item)]
                scene = pick_first_str(model_result.get("scene", scene)) or scene
        output = f"objects={objects}; scene={scene}"
        return {**state, "objects": objects, "scene": scene, "output": output}

    def _model_perception(self, text: str) -> dict[str, Any] | None:
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
        group = self.prompt_group or "perception"
        return build_prompt(group, variables={"input": text})

    @staticmethod
    def _heuristic_perception(text: str) -> tuple[list[str], str]:
        lower = normalize_text(text)
        objects: list[str] = []
        known = [
            "杯子",
            "瓶子",
            "盒子",
            "螺丝",
            "螺母",
            "apple",
            "bottle",
            "box",
            "bolt",
            "nut",
        ]
        for item in known:
            if item in lower:
                objects.append(item)
        scene = "unknown scene"
        if any(word in lower for word in ["桌", "table", "desk"]):
            scene = "on a table"
        if any(word in lower for word in ["地", "floor", "ground"]):
            scene = "on the floor"
        return objects, scene

    def as_subagent(self) -> SubAgent:
        return build_subagent(
            name="perception",
            description="Extract objects and scene cues from commands or context.",
            graph=self.graph,
        )


def create_perception_subagent(
    model: BaseChatModel | None = None,
    *,
    prompt_group: str | None = None,
    prompt_path: str | None = None,
) -> SubAgent:
    return PerceptionAgent(
        model=model,
        prompt_group=prompt_group,
        prompt_path=prompt_path,
    ).as_subagent()
