"""Export Claude Code prompts (the messages typed by the user) from a local session history to Markdown.

Usage:  python scripts/export_prompts.py <session.jsonl> <output.md> [--member NAME] [--from N] [--to M] [--title TEXT]
Session files live in  ~/.claude/projects/<project-folder>/*.jsonl  on the machine where the work was done.
Only messages typed by the user are written, unchanged (system reminders and tool output are dropped).
With --from/--to only prompts N..M are written (the original numbers are kept) and --title replaces the heading, so a
part of one session can be labelled for what it is. Review the output for secrets before committing it.
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


def option(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    member = option("--member", "member")
    first, last = int(option("--from", 1)), int(option("--to", 10**9))
    everything = list(user_messages(sys.argv[1]))
    chosen = [(n, s, x) for n, (s, x) in enumerate(everything, 1) if first <= n <= last]
    heading = option("--title", f"Prompt log of {member}")
    with open(sys.argv[2], "w", encoding="utf-8", newline="\n") as out:
        out.write(
            f"# {heading}\n\nExported with scripts/export_prompts.py from a session of "
            f"{len(everything)} prompts; this file has {len(chosen)} "
            f"(numbers {first}-{min(last, len(everything))}), unchanged.\n"
        )
        out.writelines(
            f"\n## Prompt {n} ({stamp})\n\n````text\n{text}\n````\n" for n, stamp, text in chosen
        )
    print("wrote", len(chosen), "prompts to", sys.argv[2])


if __name__ == "__main__":
    main()
