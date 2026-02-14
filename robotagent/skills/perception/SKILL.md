---
name: perception
description: Define and maintain the perception subagent that extracts objects and scene cues from user inputs. Use when updating object vocabularies, scene rules, or perception-related prompts.
---

# Perception Subagent

## Overview
Extract objects of interest and coarse scene context from user commands or text context.

## Workflow
1. Maintain a small vocabulary of common objects and scene hints.
2. Keep model prompt output JSON-friendly with keys: `objects`, `scene`.
3. Ensure the subagent returns both structured fields and a concise `output` string.

## Output Contract
Return at least:
- `objects`: list of strings
- `scene`: short description
- `output`: summary string
