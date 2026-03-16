"""FTS5 search across indexed sessions."""

from __future__ import annotations

import re
import sqlite3


def sanitize_query(query: str) -> str:
    """Sanitize a user query for FTS5.

    FTS5 has its own query syntax. User queries may contain characters
    that break parsing (backticks, unbalanced parens, etc.). This function
    makes arbitrary user input safe for FTS5 MATCH.
    """
    # Remove backticks (markdown code fences)
    q = query.replace("`", "")

    # Remove unbalanced parentheses
    depth = 0
    chars = []
    for c in q:
        if c == "(":
            depth += 1
            chars.append(c)
        elif c == ")":
            if depth > 0:
                depth -= 1
                chars.append(c)
            # else: skip unmatched closing paren
        else:
            chars.append(c)
    # Remove unmatched opening parens
    q = "".join(chars)
    while q.count("(") > q.count(")"):
        idx = q.rfind("(")
        q = q[:idx] + q[idx + 1 :]

    # Collapse multiple spaces
    q = re.sub(r"\s+", " ", q).strip()

    # If empty after sanitization, return a no-match query
    if not q:
        return '""'

    return q


def search_sessions(
    conn: sqlite3.Connection,
    query: str,
    project: str | None = None,
    limit: int = 5,
) -> list[dict]:
    """Search indexed sessions using FTS5.

    Args:
        conn: SQLite connection with initialized schema.
        query: Search query (will be sanitized for FTS5).
        project: Optional project filter.
        limit: Maximum number of sessions to return.

    Returns:
        List of session dicts with matched message snippets.
    """
    safe_query = sanitize_query(query)

    # Search messages via FTS5, join with sessions for metadata
    sql = """
        SELECT
            s.session_id,
            s.slug,
            s.project,
            s.started_at,
            s.message_count,
            s.summary,
            m.role,
            snippet(messages_fts, 0, '>>>', '<<<', '...', 40) AS snippet,
            m.timestamp AS msg_timestamp,
            rank
        FROM messages_fts
        JOIN messages m ON m.id = messages_fts.rowid
        JOIN sessions s ON s.session_id = m.session_id
        WHERE messages_fts MATCH ?
    """
    params: list = [safe_query]

    if project:
        sql += " AND s.project = ?"
        params.append(project)

    sql += " ORDER BY rank LIMIT ?"
    params.append(limit * 3)  # Fetch more to group by session

    try:
        rows = conn.execute(sql, params).fetchall()
    except sqlite3.OperationalError:
        # FTS5 query syntax error despite sanitization
        return []

    # Group by session
    sessions: dict[str, dict] = {}
    for row in rows:
        sid = row["session_id"]
        if sid not in sessions:
            sessions[sid] = {
                "session_id": sid,
                "slug": row["slug"],
                "project": row["project"],
                "started_at": row["started_at"],
                "message_count": row["message_count"],
                "summary": row["summary"],
                "matched_messages": [],
            }
        sessions[sid]["matched_messages"].append(
            {
                "role": row["role"],
                "snippet": row["snippet"],
                "timestamp": row["msg_timestamp"],
            }
        )

    # Return top N sessions
    result = list(sessions.values())[:limit]
    return result
