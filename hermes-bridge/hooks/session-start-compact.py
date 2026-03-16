"""SessionStart[compact] hook: injects checkpoint summary after compaction."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from hermes_bridge.checkpoint import restore_checkpoint
from hermes_bridge.db import get_connection, init_db

LOG_DIR = Path(__file__).resolve().parent.parent / "data"
LOG_FILE = LOG_DIR / "hooks.log"


def log(msg: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now(timezone.utc).isoformat()}] session-start-compact: {msg}\n")


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception as e:
        log(f"ERROR reading stdin: {e}")
        return

    session_id = payload.get("session_id")
    if not session_id:
        log(f"Missing session_id. Keys: {sorted(payload.keys())}")
        return

    try:
        conn = get_connection()
        init_db(conn)
        checkpoint = restore_checkpoint(conn, session_id=session_id)
        conn.close()

        if checkpoint is None:
            log(f"No checkpoint found for {session_id}")
            return

        # Build context injection
        parts = [f"[HERMES-BRIDGE CONTEXT RECOVERY] Checkpoint from {checkpoint['created_at']}:"]
        parts.append(checkpoint["summary"])

        if checkpoint.get("key_decisions"):
            parts.append("\nKey decisions: " + "; ".join(checkpoint["key_decisions"]))
        if checkpoint.get("files_changed"):
            parts.append("\nFiles changed: " + ", ".join(checkpoint["files_changed"]))

        context = "\n".join(parts)

        # Inject via additionalContext
        result = {
            "hookSpecificOutput": {
                "additionalContext": context,
            }
        }
        json.dump(result, sys.stdout)
        log(f"Injected checkpoint for {session_id} ({len(context)} chars)")
    except Exception as e:
        log(f"ERROR restoring checkpoint for {session_id}: {e}")


if __name__ == "__main__":
    main()
