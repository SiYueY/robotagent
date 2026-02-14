---
name: execution
description: Define and maintain the execution-planning subagent for robot commands. Use when updating plan templates, action lists, or execution-related prompts and parsing.
---

# Execution Subagent

## Overview
Produce an execution plan and low-level action list given a user command.

## Workflow
1. Keep action templates concise and deterministic.
2. Prefer heuristic-first planning with optional model refinement.
3. Ensure the subagent returns both structured fields and a concise `output` string.

## Output Contract
Return at least:
- `plan`: list of steps
- `actions`: list of low-level actions
- `output`: summary string
