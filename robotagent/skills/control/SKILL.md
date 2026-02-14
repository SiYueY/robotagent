---
name: control
description: Build or update the robot control agent in this repo, including intent, perception, and execution subagents, their LangGraph flows, and the deepagent wiring in `robotagent/agents/robot_agent.py`.
---

# Robot Control Agent

## Overview
Define the robot control workflow as three subagents: intent recognition, perception parsing, and execution planning. Use this skill when adding capabilities, changing prompts, or updating the subagent graphs.

## Core Capabilities
1. Intent recognition for robot commands (pick/place/move/stop).
2. Perception extraction (objects, scene cues) from user input.
3. Execution planning (high-level plan and low-level actions).

## Workflow
1. Update or create subagents under `robotagent/agents/subagent/`.
2. Keep each subagent a single-node `StateGraph` unless multi-step reasoning is required.
3. Prefer heuristic-first logic with optional model refinement to avoid brittle parsing.
4. Ensure each subagent returns a compact `output` string plus structured fields.
5. Wire subagents into `RobotAgent` in `robotagent/agents/robot_agent.py`.

## Subagent Patterns
- Intent: classify into `pick`, `place`, `move`, `stop`, or `unknown` with confidence.
- Perception: extract `objects` and `scene` hints from the text.
- Execution: produce `plan` and `actions` lists for downstream execution.

## Integration Notes
- `RobotAgent` should pass a single shared chat model into all subagents.
- Avoid importing deleted wrappers; use `deepagents.create_deep_agent` directly.
- Keep any new prompts concise and JSON-friendly to improve parsing.

## Output Contract
Each subagent should return:
- Structured fields (e.g., `intent`, `objects`, `plan`)
- A human-readable `output` summary
