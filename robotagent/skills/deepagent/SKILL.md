---
name: deepagent
description: Build or update Deepagent-based agents in this repo, including wiring memory (AGENTS.md), skills directories, and subagent definitions. Use when creating a new Deepagent, adding skills, or configuring subagent graphs/tools for a multi-agent workflow.
---

# Deepagent Integration

## Overview
Define a Deepagent by files on disk and a small wiring script. Use this skill to create or update the memory/skills/subagents layout and connect it to `create_deep_agent`.

## Workflow
1. Identify the agent root directory and confirm where `AGENTS.md`, `skills/`, and `subagents.yaml` should live.
2. Ensure `AGENTS.md` contains stable, always-on guidance (voice, safety, constraints).
3. Create or update skills under `skills/<skill-name>/SKILL.md` with task-specific workflows.
4. Define subagents in code (or load from YAML) with clear `name`, `description`, and tools.
5. Wire everything into `create_deep_agent(...)` with `memory`, `skills`, and `subagents`.

## File Map
- `AGENTS.md`: Persistent context loaded into system prompt.
- `skills/<skill>/SKILL.md`: On-demand workflows.
- `subagents.yaml` (optional): Externalized definitions loaded by a helper.
- `*.py`: Tool definitions and the deepagent wiring code.

## Deepagent Wiring Pattern
Use this structure when creating a new agent:

```python
agent = create_deep_agent(
    model=model,
    memory=["./AGENTS.md"],
    skills=["./skills/"],
    subagents=subagents,
    tools=tools,
    backend=FilesystemBackend(root_dir="./"),
)
```

## Subagent Guidelines
- Keep each subagent focused on a single responsibility (e.g., research, planning, execution).
- Provide deterministic outputs where possible (structured fields or JSON snippets).
- Use lightweight tools first; only add web/search tools when required.

## Quality Checklist
- `AGENTS.md` covers stable constraints only.
- Skills are minimal and task-focused; avoid duplicating global guidance.
- Subagents have non-overlapping roles and explicit tool lists.
- The wiring code uses explicit paths relative to the agent root.
