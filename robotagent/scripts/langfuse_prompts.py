from __future__ import annotations

import argparse
import json
from pathlib import Path

from robotagent.prompts.langfuse_prompt_manager import (
    export_prompt_group,
    langfuse_spec,
    list_groups,
    upload_prompt_group,
)


def _cmd_list(args: argparse.Namespace) -> int:
    groups = list_groups()
    if not groups:
        print("No prompt groups found.")
        return 0

    for group in groups:
        spec = langfuse_spec(group)
        if args.details:
            print(f"{group}: {spec}")
            continue
        name = spec.get("name") or group
        label = spec.get("label") or "production"
        prompt_type = spec.get("type") or "text"
        print(f"{group}: name={name} label={label} type={prompt_type}")

    return 0


def _cmd_push(args: argparse.Namespace) -> int:
    groups = list_groups()
    if args.group:
        groups = [group for group in groups if group in set(args.group)]

    if not groups:
        print("No prompt groups selected.")
        return 0

    for group in groups:
        msg = upload_prompt_group(
            group,
            label=args.label,
            prompt_type=args.prompt_type,
            name=args.name,
            dry_run=args.dry_run,
        )
        if msg:
            print(msg)

    return 0


def _cmd_pull(args: argparse.Namespace) -> int:
    variables = None
    if args.vars:
        variables = json.loads(args.vars)

    output_path = Path(args.out) if args.out else None
    path = export_prompt_group(args.group, variables=variables, output_path=output_path)
    print(f"[ok] exported to {path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage Langfuse prompts")
    sub = parser.add_subparsers(dest="command", required=True)

    list_parser = sub.add_parser("list", help="List prompt groups and Langfuse specs")
    list_parser.add_argument("--details", action="store_true", help="Show full Langfuse spec")
    list_parser.set_defaults(func=_cmd_list)

    push_parser = sub.add_parser("push", help="Upload local prompt files to Langfuse")
    push_parser.add_argument("--group", action="append", help="Only upload these prompt groups")
    push_parser.add_argument("--label", help="Override prompt label")
    push_parser.add_argument("--type", dest="prompt_type", help="Override prompt type")
    push_parser.add_argument("--name", help="Override prompt name")
    push_parser.add_argument("--dry-run", action="store_true", help="Print actions without uploading")
    push_parser.set_defaults(func=_cmd_push)

    pull_parser = sub.add_parser("pull", help="Export prompt content from Langfuse")
    pull_parser.add_argument("group", help="Prompt group name")
    pull_parser.add_argument("--out", help="Output file path")
    pull_parser.add_argument("--vars", help="JSON variables for template compilation")
    pull_parser.set_defaults(func=_cmd_pull)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
