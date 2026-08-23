# callsheet-agent

The stage-manager side of [callsheet](https://github.com/prismatic7/callsheet),
a calm day-board for macOS. This repo lets any Hermes Agent user give their
callsheet board an agent layer: a daily job that reads the day and proposes
**ghost cards** — dashed, quiet suggestions the user can commit or dismiss.

The board never pings. The ghost cards are the message.

```
┌─────────────────────────────────────────────┐
│ Hermes (cron, 07:00)                        │
│   reads day → consults memory → proposes    │
│         │                                   │
│         ▼  writes (same SQLite store)       │
│   callsheet-propose.py                      │
│         │                                   │
│         ▼                                   │
│  callsheet app (WAL-safe)                   │
│   ┌───────────────────────────┐             │
│   │ 9am — **Rehearse** Scene 2 │             │
│   │ ::::::::::::::::::::::::::: │  ← ghost    │
│   └───────────────────────────┘  (dashed)   │
└─────────────────────────────────────────────┘
```

## Requirements

- The [callsheet](https://github.com/prismatic7/callsheet) app built and run
  at least once (creates the SQLite store + migrations)
- Hermes Agent with the cron system (any recent version)
- macOS (the default DB path is macOS-specific)

## Install

1. **Copy the script:**

   ```bash
   mkdir -p ~/.hermes/scripts
   cp scripts/callsheet-propose.py ~/.hermes/scripts/
   chmod +x ~/.hermes/scripts/callsheet-propose.py
   ```

2. **Install the skill:**

   ```bash
   mkdir -p ~/.hermes/skills/meta
   cp -R skills/callsheet-agent ~/.hermes/skills/meta/
   ```

3. **Create the daily job** — see
   [`cron/callsheet-daily-proposals.md`](cron/callsheet-daily-proposals.md)
   for the exact `hermes cron create` command and prompt. The short version:

   ```bash
   hermes cron create --name callsheet-daily-proposals --deliver local \
     --skill callsheet-agent "0 7 * * *" "<prompt from the cron file>"
   ```

   `--deliver local` is the point: nothing is pushed to any channel. The
   ghosts appear in the board.

4. **Non-default DB path?** If you build callsheet with a different Tauri
   identifier, export `CALLSHEET_DB` in the cron service's environment or
   pass `--db` in every command.

## Usage

The script is a stdlib-only CLI:

```bash
# Read a day (JSON, incl. ghosts)
python3 ~/.hermes/scripts/callsheet-propose.py list --date 2026-08-23

# Propose a ghost card
python3 ~/.hermes/scripts/callsheet-propose.py propose \
  --date 2026-08-23 --type research --markdown "**Draft** *Phase C header*" --source agent

# Dismiss a card (ghost or real)
python3 ~/.hermes/scripts/callsheet-propose.py dismiss --id 42
```

DB path resolution: `--db` → `CALLSHEET_DB` → default macOS path
(`~/Library/Application Support/com.chris.callsheet/callsheet.db`).

## Files

| Path | Purpose |
|---|---|
| `scripts/callsheet-propose.py` | stdlib-only SQLite CLI: `list` / `propose` / `dismiss` |
| `skills/callsheet-agent/SKILL.md` | Agent guidance: quality bar, workflow, pitfalls |
| `cron/callsheet-daily-proposals.md` | exact cron command + prompt to recreate the daily job |

## Safety

- The script is stdlib-only — no network, no deps, no secrets
- Parameterized SQL only — never string-concatenates input
- WAL-safe: `busy_timeout 5000` means a write never dies with `SQLITE_BUSY`
  while the app is reading
- `dismiss` deletes any card by id — ghost **or real**. The skill warns the
  agent to never dismiss real cards unless explicitly asked

## License

MIT — see [LICENSE](LICENSE).
