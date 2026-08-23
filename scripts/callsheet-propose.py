#!/usr/bin/env python3
"""callsheet-propose.py — agent write path for the Callsheet day board.

Hermes/Noema (the "stage manager") uses this CLI to read a day and propose
ghost cards. The board never pings: proposals appear as dashed cards the
user can commit or dismiss.

Commands
--------
  list    --date YYYY-MM-DD            JSON of the day's cards (incl. ghosts)
  propose --date YYYY-MM-DD --type <id|name> --markdown "..." [--source agent]
                                       insert a ghost card at the end of the day
  dismiss --id N                       delete a card (ghost or real)

DB path
-------
Resolution order:
1. --db flag
2. CALLSHEET_DB environment variable
3. Default (macOS): ~/Library/Application Support/com.chris.callsheet/callsheet.db
   (stable for the Tauri identifier com.chris.callsheet — see
   src-tauri/tauri.conf.json in the callsheet repo). Users who build the app
   with a different identifier should set CALLSHEET_DB or pass --db.

Safety
------
- stdlib only (sqlite3, argparse, json, os, sys, pathlib)
- parameterized SQL only — never string-concatenate user input
- WAL-safe: sets busy_timeout 5000 so a write never dies with SQLITE_BUSY
  while the app is reading
- no secrets, no network, no deps
- exits non-zero with a clear message on failure
"""

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path

DEFAULT_DB = (
    Path.home()
    / "Library"
    / "Application Support"
    / "com.chris.callsheet"
    / "callsheet.db"
)

BUSY_TIMEOUT_MS = 5000


def connect(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        sys.exit(f"error: database not found at {db_path}")
    conn = sqlite3.connect(str(db_path), timeout=BUSY_TIMEOUT_MS / 1000)
    conn.execute(f"PRAGMA busy_timeout = {BUSY_TIMEOUT_MS}")
    return conn


def has_source_column(conn: sqlite3.Connection) -> bool:
    row = conn.execute(
        "SELECT COUNT(*) FROM pragma_table_info('cards') WHERE name = 'source'"
    ).fetchone()
    return bool(row and row[0] > 0)


def resolve_type_id(conn: sqlite3.Connection, type_ref: str) -> int:
    """Resolve --type as an id (digits) or a name (case-insensitive)."""
    if type_ref.isdigit():
        return int(type_ref)
    row = conn.execute(
        "SELECT id FROM activity_types WHERE name = ?1 COLLATE NOCASE",
        (type_ref,),
    ).fetchone()
    if row is None:
        sys.exit(f"error: unknown activity type '{type_ref}'")
    return row[0]


def cmd_list(conn: sqlite3.Connection, args) -> None:
    if has_source_column(conn):
        rows = conn.execute(
            "SELECT id, date, activity_type_id, position, markdown, is_ghost, source "
            "FROM cards WHERE date = ?1 ORDER BY position ASC",
            (args.date,),
        ).fetchall()
        cards = [
            {
                "id": r[0],
                "date": r[1],
                "activityTypeId": r[2],
                "position": r[3],
                "markdown": r[4],
                "isGhost": bool(r[5]),
                "source": r[6],
            }
            for r in rows
        ]
    else:
        # Pre-source schema (app not yet launched with the migration).
        rows = conn.execute(
            "SELECT id, date, activity_type_id, position, markdown, is_ghost "
            "FROM cards WHERE date = ?1 ORDER BY position ASC",
            (args.date,),
        ).fetchall()
        cards = [
            {
                "id": r[0],
                "date": r[1],
                "activityTypeId": r[2],
                "position": r[3],
                "markdown": r[4],
                "isGhost": bool(r[5]),
                "source": None,
            }
            for r in rows
        ]
    print(json.dumps(cards, ensure_ascii=False))


def cmd_propose(conn: sqlite3.Connection, args) -> None:
    type_id = resolve_type_id(conn, args.type)
    position = conn.execute(
        "SELECT COALESCE(MAX(position) + 1, 0) FROM cards WHERE date = ?1",
        (args.date,),
    ).fetchone()[0]
    if has_source_column(conn):
        conn.execute(
            "INSERT INTO cards (date, activity_type_id, position, markdown, is_ghost, source) "
            "VALUES (?1, ?2, ?3, ?4, 1, ?5)",
            (args.date, type_id, position, args.markdown, args.source),
        )
    else:
        # Pre-source schema (app not yet launched with the migration): the
        # column will appear on next launch; the ghost is still valid.
        conn.execute(
            "INSERT INTO cards (date, activity_type_id, position, markdown, is_ghost) "
            "VALUES (?1, ?2, ?3, ?4, 1)",
            (args.date, type_id, position, args.markdown),
        )
    conn.commit()
    print(json.dumps({"ok": True, "id": conn.execute("SELECT last_insert_rowid()").fetchone()[0]}))


def cmd_dismiss(conn: sqlite3.Connection, args) -> None:
    cur = conn.execute("DELETE FROM cards WHERE id = ?1", (args.id,))
    conn.commit()
    if cur.rowcount == 0:
        sys.exit(f"error: no card with id {args.id}")
    print(json.dumps({"ok": True, "deleted": args.id}))


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="callsheet-propose",
        description="Read a day and propose ghost cards for the Callsheet board.",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=Path(os.environ.get("CALLSHEET_DB", DEFAULT_DB)),
        help="SQLite DB path (env: CALLSHEET_DB)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="list a day's cards as JSON")
    p_list.add_argument("--date", required=True, help="YYYY-MM-DD")

    p_propose = sub.add_parser("propose", help="insert a ghost card")
    p_propose.add_argument("--date", required=True, help="YYYY-MM-DD")
    p_propose.add_argument("--type", required=True, help="activity type id or name")
    p_propose.add_argument("--markdown", required=True, help="card content")
    p_propose.add_argument("--source", default="agent", help="proposal source (default: agent)")

    p_dismiss = sub.add_parser("dismiss", help="delete a card by id")
    p_dismiss.add_argument("--id", type=int, required=True, help="card id")

    args = parser.parse_args()
    conn = connect(args.db)
    try:
        if args.command == "list":
            cmd_list(conn, args)
        elif args.command == "propose":
            cmd_propose(conn, args)
        elif args.command == "dismiss":
            cmd_dismiss(conn, args)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
