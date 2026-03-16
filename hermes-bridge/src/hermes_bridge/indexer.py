"""JSONL session indexer for Claude Code transcript files."""

from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)


def _extract_text_content(content: str | list | dict) -> str | None:
    """Extract plain text from a message content field.

    Claude Code JSONL stores content as:
    - A plain string
    - A list of content blocks (each with "type" key)
    - A dict with "type" key

    We only want text blocks, skipping tool_use, tool_result, and thinking.
    """
    if isinstance(content, str):
        return content if content.strip() else None

    if isinstance(content, dict):
        if content.get("type") == "text":
            return content.get("text", "")
        return None

    if isinstance(content, list):
        text_parts = []
        for block in content:
            if isinstance(block, str):
                text_parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                text = block.get("text", "")
                if text.strip():
                    text_parts.append(text)
        return "\n".join(text_parts) if text_parts else None

    return None


def index_session(conn: sqlite3.Connection, jsonl_path: Path, project: str) -> dict:
    """Index a Claude Code JSONL session transcript into the database.

    Args:
        conn: SQLite connection (must have schema initialized).
        jsonl_path: Path to the .jsonl transcript file.
        project: Project identifier (e.g., "C--Users-Anderfail-appendix-k").

    Returns:
        Dict with indexing stats: {session_id, message_count, tool_use_count, slug}.
    """
    session_id: str | None = None
    slug: str | None = None
    cwd: str | None = None
    git_branch: str | None = None
    started_at: str | None = None
    ended_at: str | None = None
    tool_use_count = 0

    # Collect messages, deduplicating assistant streaming chunks by requestId
    messages: list[dict] = []
    seen_request_ids: dict[str, int] = {}  # requestId -> index in messages list

    with open(jsonl_path, encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                logger.warning("Skipping malformed JSON at %s:%d", jsonl_path, line_num)
                continue

            # Extract session metadata from any entry
            if session_id is None:
                session_id = entry.get("sessionId")
            if slug is None:
                slug = entry.get("slug")
            elif entry.get("slug"):
                slug = entry["slug"]  # Update slug if found later
            if cwd is None:
                cwd = entry.get("cwd")
            if git_branch is None:
                git_branch = entry.get("gitBranch")

            # Track timestamps
            ts = entry.get("timestamp")
            if ts:
                if started_at is None or ts < started_at:
                    started_at = ts
                if ended_at is None or ts > ended_at:
                    ended_at = ts

            entry_type = entry.get("type")

            # Skip non-conversation entries
            if entry_type in ("system", "progress", "file-history-snapshot"):
                continue

            # Extract message content
            message = entry.get("message", {})
            role = message.get("role")
            if role not in ("user", "assistant"):
                continue

            content = message.get("content")
            if content is None:
                continue

            text = _extract_text_content(content)
            if not text or not text.strip():
                # Check for tool_use (count but don't index)
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "tool_use":
                            tool_use_count += 1
                continue

            timestamp = entry.get("timestamp", "")

            # Deduplicate assistant streaming chunks by requestId
            request_id = entry.get("requestId")
            if role == "assistant" and request_id and request_id in seen_request_ids:
                # Append to existing message
                idx = seen_request_ids[request_id]
                messages[idx]["content"] += "\n" + text
                messages[idx]["timestamp"] = timestamp  # Use latest timestamp
            else:
                idx = len(messages)
                messages.append(
                    {
                        "role": role,
                        "content": text,
                        "timestamp": timestamp,
                    }
                )
                if role == "assistant" and request_id:
                    seen_request_ids[request_id] = idx

    if session_id is None:
        raise ValueError(f"No sessionId found in {jsonl_path}")

    # Upsert session
    conn.execute(
        """INSERT INTO sessions (session_id, slug, project, started_at, ended_at, cwd,
                                 git_branch, message_count, tool_use_count)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(session_id) DO UPDATE SET
               slug = COALESCE(excluded.slug, sessions.slug),
               started_at = COALESCE(excluded.started_at, sessions.started_at),
               ended_at = COALESCE(excluded.ended_at, sessions.ended_at),
               cwd = COALESCE(excluded.cwd, sessions.cwd),
               git_branch = COALESCE(excluded.git_branch, sessions.git_branch),
               message_count = excluded.message_count,
               tool_use_count = excluded.tool_use_count,
               indexed_at = datetime('now')""",
        (
            session_id,
            slug,
            project,
            started_at,
            ended_at,
            cwd,
            git_branch,
            len(messages),
            tool_use_count,
        ),
    )

    # Delete old messages for re-indexing
    conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))

    # Insert messages
    for msg in messages:
        conn.execute(
            "INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
            (session_id, msg["role"], msg["content"], msg["timestamp"]),
        )

    conn.commit()

    return {
        "session_id": session_id,
        "message_count": len(messages),
        "tool_use_count": tool_use_count,
        "slug": slug,
    }
