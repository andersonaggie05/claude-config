"""Context checkpoint management for surviving compaction."""

from __future__ import annotations

import json
import sqlite3

MAX_SUMMARY_CHARS = 2000


def save_checkpoint(
    conn: sqlite3.Connection,
    session_id: str,
    summary: str,
    key_decisions: list[str] | None = None,
    files_changed: list[str] | None = None,
) -> int:
    """Save a context checkpoint before compaction.

    Args:
        conn: SQLite connection with initialized schema.
        session_id: Current session ID.
        summary: Summary of current context state.
        key_decisions: List of key decisions made so far.
        files_changed: List of files modified in this session.

    Returns:
        Checkpoint ID.
    """
    # Enforce summary size limit
    if len(summary) > MAX_SUMMARY_CHARS:
        summary = summary[: MAX_SUMMARY_CHARS - 3] + "..."

    cursor = conn.execute(
        """INSERT INTO checkpoints (session_id, summary, key_decisions, files_changed)
           VALUES (?, ?, ?, ?)""",
        (
            session_id,
            summary,
            json.dumps(key_decisions) if key_decisions else None,
            json.dumps(files_changed) if files_changed else None,
        ),
    )
    conn.commit()
    return cursor.lastrowid  # type: ignore[return-value]


def restore_checkpoint(
    conn: sqlite3.Connection,
    session_id: str | None = None,
) -> dict | None:
    """Restore the latest checkpoint for a session.

    Args:
        conn: SQLite connection with initialized schema.
        session_id: Session ID to restore from. If None, returns the most recent checkpoint.

    Returns:
        Dict with checkpoint data, or None if no checkpoint found.
    """
    if session_id:
        row = conn.execute(
            """SELECT id, session_id, summary, key_decisions, files_changed, created_at
               FROM checkpoints
               WHERE session_id = ?
               ORDER BY id DESC LIMIT 1""",
            (session_id,),
        ).fetchone()
    else:
        row = conn.execute(
            """SELECT id, session_id, summary, key_decisions, files_changed, created_at
               FROM checkpoints
               ORDER BY id DESC LIMIT 1""",
        ).fetchone()

    if row is None:
        return None

    return {
        "checkpoint_id": row["id"],
        "session_id": row["session_id"],
        "summary": row["summary"],
        "key_decisions": json.loads(row["key_decisions"]) if row["key_decisions"] else [],
        "files_changed": json.loads(row["files_changed"]) if row["files_changed"] else [],
        "created_at": row["created_at"],
    }
