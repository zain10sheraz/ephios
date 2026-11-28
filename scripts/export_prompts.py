"""Export your own Claude Code prompts (the messages you typed) from the local session history to Markdown.

Usage:  python scripts/export_prompts.py <session.jsonl> <output.md> [--member NAME]
Session files live in  ~/.claude/projects/<project-folder>/*.jsonl  on the machine where you worked.
Only messages typed by the user are written, unchanged (system reminders and tool output are dropped).
Review the output for secrets (tokens, passwords) before committing it.
"""

import json
import re
import sys


def user_messages(path):
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if row.get("type") != "user" or row.get("isSidechain") or row.get("toolUseResult"):
                continue
            content = row["message"].get("content")
            if isinstance(content, list):
                content = "\n".join(
                    part.get("text", "")
                    for part in content
                    if isinstance(part, dict) and part.get("type") == "text"
                )
            content = re.sub(
                r"<system-reminder>.*?</system-reminder>", "", content or "", flags=re.DOTALL
            ).strip()
            if content and not content.startswith("<"):
                yield row.get("timestamp", ""), content


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    member = sys.argv[sys.argv.index("--member") + 1] if "--member" in sys.argv else "member"
    messages = list(user_messages(sys.argv[1]))
    with open(sys.argv[2], "w", encoding="utf-8", newline="\n") as out:
        out.write(
            f"# Prompt log of {member}\n\nExported with scripts/export_prompts.py; "
            f"{len(messages)} prompts, unchanged.\n"
        )
        out.writelines(
            f"\n## Prompt {number} ({stamp})\n\n````text\n{text}\n````\n"
            for number, (stamp, text) in enumerate(messages, 1)
        )
    print("wrote", len(messages), "prompts to", sys.argv[2])


if __name__ == "__main__":
    main()
