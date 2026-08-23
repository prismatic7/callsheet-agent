# callsheet-agent — Agent Guide

The stage-manager side of the callsheet day board. This repo ships the pieces
that let a Hermes Agent user give their callsheet board an agent layer: a
stdlib-only SQLite CLI, a skill with the proposal quality bar, and the exact
cron command to recreate the daily ghost-card job.

## Structure

```
scripts/callsheet-propose.py        stdlib-only CLI (list / propose / dismiss)
skills/callsheet-agent/SKILL.md     agent guidance (quality bar, workflow)
cron/callsheet-daily-proposals.md   exact hermes cron create command + prompt
README.md                           install + usage
LICENSE                             MIT
```

## Conventions

- **The script is the only executable.** Skills and cron files are guidance —
  they reference `~/.hermes/scripts/callsheet-propose.py`, never inline SQL.
- **The script stays stdlib-only.** No pip deps, no network, no secrets.
  If a change needs a third-party library, that's a design discussion, not a
  drive-by import.
- **Parameterized SQL only.** Never string-concatenate user input (the
  script's `resolve_type_id` and insert paths are the pattern to keep).
- **DB path resolution is `--db` → `CALLSHEET_DB` → default macOS path.**
  Keep this order. Users with non-default Tauri identifiers need the env
  override.
- **The skill's quality bar is the product.** Terse ghosts, ≤3/day,
  day-scoped, markdown-styled, `--source agent` for cron proposals,
  deliver=local. Never edit the skill to make the agent louder.
- **No pings.** The ghosts are the message. `--deliver local` in the cron
  template is a commitment, not an accident.
- **No Chris-specific content.** The skill's consultation order is a
  portable template (pattern memory → project state → known preferences),
  not a reference to anyone's vault or preferences.

## Verification

After any change:

1. `python3 -m py_compile scripts/callsheet-propose.py`
2. Smoke test against a scratch DB (see README workflow):
   create a temp DB with the callsheet schema, `list`, `propose`, `dismiss`
   must all round-trip cleanly.
3. `hermes cron create --help` to confirm the CLI shape still matches the
   cron template before editing the template.
4. Keep README, skill, and cron template in sync when behaviour changes.
