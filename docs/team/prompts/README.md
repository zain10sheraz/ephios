# Prompt logs

One file per member, exported unchanged from that member's own Claude Code history:

```
python scripts/export_prompts.py ~/.claude/projects/<project-folder>/<session>.jsonl docs/team/prompts/ZAIN_PROMPTS.md --member Zain
```

Files expected: `ZAIN_PROMPTS.md`, `MANAN_PROMPTS.md`, `SAJAWAL_PROMPTS.md`. Each member runs the script on the
machine where they worked and commits the result under their own account. Check each file for tokens or passwords
before committing.
