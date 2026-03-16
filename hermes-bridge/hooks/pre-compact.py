"""PreCompact hook: saves a context checkpoint before compaction."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from hermes_bridge.checkpoint import save_checkpoint
from hermes_bridge.db import get_connection, init_db
from hermes_bridge.indexer import _extract_text_content

LOG_DIR = Path(__file__).resolve().parent.parent / "data"
LOG_FILE = LOG_DIR / "hooks.log"


def log(msg: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now(timezone.utc).isoformat()}] pre-compact: {msg}\n")


def extract_recent_context(transcript_path: str, max_exchanges: int = 20) -> str:
    """Extract the last N user/assistant text exchanges from a transcript."""
    path = Path(transcript_path)
    if not path.exists():
        return ""

    exchanges: list[str] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            entry_type = entry.get("type")
            if entry_type not in ("user", "assistant"):
                continue

            message = entry.get("message", {})
            role = message.get("role", "")
            content = message.get("content")
            if content is None:
                continue

            text = _extract_text_content(content)
            if text and text.strip():
                exchanges.append(f"[{role}]: {text.strip()}")

    # Take last N exchanges
    recent = exchanges[-max_exchanges:]
    return "\n\n".join(recent)


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

    try:
        summary = extract_recent_context(transcript_path)
        if not summary:
            log(f"No text content to checkpoint for {session_id}")
            return

        conn = get_connection()
        init_db(conn)
        checkpoint_id = save_checkpoint(conn, session_id, summary)
        conn.close()
        log(f"Saved checkpoint {checkpoint_id} for session {session_id} ({len(summary)} chars)")
    except Exception as e:
        log(f"ERROR checkpointing {session_id}: {e}")


if __name__ == "__main__":
    main()
