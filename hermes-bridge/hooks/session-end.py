"""SessionEnd hook: indexes the completed session into hermes-bridge SQLite."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add package to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from hermes_bridge.db import get_connection, init_db
from hermes_bridge.indexer import index_session

LOG_DIR = Path(__file__).resolve().parent.parent / "data"
LOG_FILE = LOG_DIR / "hooks.log"


def log(msg: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now(timezone.utc).isoformat()}] session-end: {msg}\n")


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception as e:
        log(f"ERROR reading stdin: {e}")
        return

    session_id = payload.get("session_id")
    transcript_path = payload.get("transcript_path")

    if not session_id or not transcript_path:
        log(f"Missing session_id or transcript_path. Keys: {sorted(payload.keys())}")
        return

    path = Path(transcript_path)
    if not path.exists():
        log(f"Transcript not found: {transcript_path}")
        return

    # Derive project from directory name
    project = path.parent.name

    try:
        conn = get_connection()
        init_db(conn)
        result = index_session(conn, path, project)
        conn.close()
        log(
            f"Indexed session {session_id} "
            f"({result['message_count']} messages, "
            f"{result['tool_use_count']} tool uses, "
            f"slug={result.get('slug')})"
        )
    except Exception as e:
        log(f"ERROR indexing {session_id}: {e}")


if __name__ == "__main__":
    main()
