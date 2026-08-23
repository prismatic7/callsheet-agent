---
name: callsheet-agent
version: 1.0.0
category: meta
description: Use when proposing ghost cards to a Callsheet day board, or when asked to suggest what to work on.
tags: [callsheet, agent-layer, ghost-cards, day-board, stage-manager]
---

# Callsheet Agent

The stage-manager side of the Callsheet day board. Hermes reads the same
SQLite store the app uses and proposes ghost cards — dashed, quiet
suggestions the user can commit or dismiss. The board never pings; the
ghost cards are the message.

## When to Activate

- Daily proposal run (cron, suggested 07:00 local)
- "What should I do today?" / "propose for tomorrow"
- Any request to add a suggestion to the Callsheet board

## The Script

`callsheet-propose.py` (in `scripts/` of this repo, copied to
`~/.hermes/scripts/`) — stdlib-only CLI:

```bash
# Read a day (JSON, incl. ghosts)
python3 ~/.hermes/scripts/callsheet-propose.py list --date YYYY-MM-DD

# Propose a ghost card (appends at end of day)
python3 ~/.hermes/scripts/callsheet-propose.py propose \
  --date YYYY-MM-DD --type <id|name> --markdown "..." --source agent

# Dismiss a card (ghost or real)
python3 ~/.hermes/scripts/callsheet-propose.py dismiss --id N
```

DB path resolution: `--db` flag → `CALLSHEET_DB` env var → the default
macOS path for the Tauri identifier `com.chris.callsheet`
(`~/Library/Application Support/com.chris.callsheet/callsheet.db`). Users
who build the app with a different identifier must set `CALLSHEET_DB` or
pass `--db` — never guess the path.

## Proposal Quality Bar

- **Terse** — a few words, not a sentence. The ghost card is a whisper, not
  an instruction. Good: `**Draft** Phase C header`. Bad: "Draft the Phase C
  script header for PIPELINE.md".
- **Markdown-styled** — the ghost card renders markdown, so use it: bold the
  verb, italic the object (`**Draft** *Phase C header*`). Plain prose reads
  like a command; styled fragments read like a suggestion.
- **≤ 3 proposals per day** — calm, not noisy. One is often enough.
- **Day-scoped** — never propose for past days. Today or tomorrow only.
- **No pings** — output is local-only. The ghost card IS the message.
- **Source is `agent`** for cron proposals (manual demo uses `manual`).

## Context Consultation Order

Before proposing, consult the user's preferred sources in this order
(adapt to what the user actually maintains):

1. **Pattern memory** — recent days' cards (`list --date <today>`) and any
   long-term memory (Noema traces, LCM, session history): what the user
   actually did, not what they said they'd do.
2. **Project state** — the user's project register / active-project note
   (e.g. an Obsidian vault): active projects, stale flags, blockers.
3. **Known preferences** — work rhythm, protected days, energy patterns
   (e.g. "Friday research, weekends personal").

If none of these exist, propose from the day's existing cards alone —
suggest the obvious next step for the highest-card activity type.

## Workflow

1. `list --date <today>` — see what's already on the board (don't duplicate)
2. Consult memory + project state (above)
3. Propose 1–3 ghosts via `propose --source agent`
4. Log a trace/note (tag `callsheet-proposals`) with what was proposed and why

## Pitfalls

- **WAL/busy_timeout**: the script sets busy_timeout 5000 — never fight the
  app's lock; a busy write fails cleanly, don't retry in a tight loop.
- **Path resolution**: never guess the DB path. `--db` or `CALLSHEET_DB`
  when the app was built with a non-default Tauri identifier.
- **Don't propose for past days** — the board is day-scoped; a ghost on
  yesterday is noise.
- **Pre-migration DBs**: if the live DB lacks the `source` column (app not
  relaunched since the migration), the script degrades gracefully — ghosts
  still insert, `source` reads as null. Don't try to ALTER the live DB from
  the script; the app migrates on next launch.
- **Never dismiss real cards** unless explicitly asked — `dismiss` deletes
  any card by id, ghost or not.

## Integration

- Cron job: daily 07:00 (suggested), deliver=local (visible not sent). The
  exact `hermes cron create` command ships in `cron/callsheet-daily-proposals.md`.
- Works with: any long-term memory (Noema, LCM), Obsidian vault (project
  register).
