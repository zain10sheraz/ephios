# Prompt logs

One file per member, exported unchanged from that member's own Claude Code history:

```
python scripts/export_prompts.py ~/.claude/projects/<project-folder>/<session>.jsonl docs/team/prompts/ZAIN_PROMPTS.md --member Zain
```

Files expected: `ZAIN_PROMPTS.md`, `MANAN_PROMPTS.md`, `SAJAWAL_PROMPTS.md`. Each member runs the script on the
machine where they worked and commits the result under their own account. Check each file for tokens or passwords
before committing.

## Files in this folder

- `ZAIN_PROMPTS.md`: the whole session, 144 prompts (screenshots EV-080, EV-080b).
- `AREA1_ZAIN_...`, `AREA2_MANAN_...`, `AREA3_SAJAWAL_and_shared_...`: the same prompts cut by area with
  `--from/--to/--title`. All of the work was done in one session on one laptop, with the GitHub account switched per area for
  the commits, so every prompt was typed by Zain; the titles say so. A member who used an AI tool on their own computer
  exports that history separately as `<NAME>_PROMPTS.md`.
