---
name: intent
description: Define and maintain the intent-recognition subagent for the robot control system. Use when updating intent classes, confidence scoring rules, or intent-related prompts and parsing.
---

# Intent Subagent

## Overview
Classify user commands into robot intent labels (pick/place/move/stop/unknown) with a confidence score and optional entities.

## Workflow
1. Update intent labels and keywords for heuristics.
2. Keep model prompt output JSON-friendly with keys: `intent`, `confidence`, `entities`.
3. Ensure the subagent returns both structured fields and a concise `output` string.

## Intent Labels
- `pick`: grasp or pick up an object
- `place`: put down or place an object
- `move`: move to a pose or location
- `stop`: halt or emergency stop
- `unknown`: unclear or unsupported command

## Output Contract
Return at least:
- `intent`: string
- `confidence`: float 0-1
- `entities`: list of strings (optional)
- `output`: summary string
