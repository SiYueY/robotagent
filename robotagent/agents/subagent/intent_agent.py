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


class IntentState(TypedDict, total=False):
    input: str
    intent: str
    confidence: float
    entities: list[str]
    output: str


class IntentRecognitionAgent:
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
        graph: StateGraph[IntentState] = StateGraph(IntentState)
        graph.add_node("classify", self._classify_intent)
        graph.set_entry_point("classify")
        graph.add_edge("classify", END)
        return graph

    def _classify_intent(self, state: IntentState) -> IntentState:
        text = state.get("input", "")
        intent, confidence, entities = self._heuristic_intent(text)
        if self.model is not None:
            model_result = self._model_intent(text)
            if model_result is not None:
                intent = pick_first_str(model_result.get("intent")) or intent
                confidence = float(model_result.get("confidence", confidence))
                raw_entities = model_result.get("entities", entities)
                if isinstance(raw_entities, list):
                    entities = [pick_first_str(item) for item in raw_entities if pick_first_str(item)]
        output = f"intent={intent}; confidence={confidence:.2f}; entities={entities}"
        return {**state, "intent": intent, "confidence": confidence, "entities": entities, "output": output}

    def _model_intent(self, text: str) -> dict[str, Any] | None:
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
        group = self.prompt_group or "intent"
        return build_prompt(group, variables={"input": text})

    @staticmethod
    def _heuristic_intent(text: str) -> tuple[str, float, list[str]]:
        lower = normalize_text(text)
        entities: list[str] = []
        if any(word in lower for word in ["抓", "取", "拿", "拾取", "pick", "grab", "grip"]):
            return "pick", 0.62, entities
        if any(word in lower for word in ["放", "放置", "放下", "place", "put", "drop"]):
            return "place", 0.6, entities
        if any(word in lower for word in ["移动", "去", "move", "go", "reach"]):
            return "move", 0.55, entities
        if any(word in lower for word in ["停止", "急停", "停下", "stop", "halt", "emergency"]):
            return "stop", 0.9, entities
        return "unknown", 0.3, entities

    def as_subagent(self) -> SubAgent:
        return build_subagent(
            name="intent",
            description="Identify user intent for robot commands.",
            graph=self.graph,
        )


def create_intent_subagent(
    model: BaseChatModel | None = None,
    *,
    prompt_group: str | None = None,
    prompt_path: str | None = None,
) -> SubAgent:
    return IntentRecognitionAgent(
        model=model,
        prompt_group=prompt_group,
        prompt_path=prompt_path,
    ).as_subagent()
