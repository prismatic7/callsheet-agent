# callsheet-daily-proposals — cron job setup

Recreates the daily ghost-card proposal job. Copy `scripts/callsheet-propose.py`
to `~/.hermes/scripts/` and the `skills/callsheet-agent/` dir to
`~/.hermes/skills/meta/callsheet-agent/` **before** creating the job (the
job's prompt references both).

## Create

```bash
hermes cron create \
  --name callsheet-daily-proposals \
  --deliver local \
  --skill callsheet-agent \
  "0 7 * * *" \
  "Run the Callsheet daily proposal workflow using the callsheet-agent skill.

1. Load the callsheet-agent skill and follow its workflow exactly.
2. Determine today's date (local time).
3. Read today's cards: python3 ~/.hermes/scripts/callsheet-propose.py list --date <today>
4. Consult the sources listed in the skill (pattern memory, project state, known preferences).
5. Propose 1-3 specific, actionable ghost cards via:
   python3 ~/.hermes/scripts/callsheet-propose.py propose --date <today> --type <id|name> --markdown \"<specific next step>\" --source agent
6. Log a Noema trace with tag callsheet-proposals describing what was proposed and why.
7. NEVER ping or deliver to any channel — the ghost cards are the message. Output is local-only.

Constraints: no more than 3 proposals, never propose for past days, never
dismiss real cards, respect the proposal quality bar in the skill."
```

Notes:
- `--deliver local` is the point: the ghosts appear in the board, nothing
  is pushed to any channel. Visible, not sent.
- `--schedule` format is cron (`minute hour day month weekday`). 07:00 is a
  suggestion — before the user's day starts so proposals are waiting.
- If the DB path is non-default, export `CALLSHEET_DB` in the shell that
  owns the cron service (or pass `--db` in every command).

## Verify

```bash
hermes cron list                 # job present
hermes cron run callsheet-daily-proposals   # manual fire to test (see docs for exact syntax)
python3 ~/.hermes/scripts/callsheet-propose.py list --date "$(date +%F)"   # ghosts visible
```
