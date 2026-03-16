"""Agent deliverable storage and retrieval for pipeline handoffs."""

from __future__ import annotations

import json
import sqlite3

from hermes_bridge.db import ARCHIVE_DAYS
from hermes_bridge.search import sanitize_query


def save_deliverable(
    conn: sqlite3.Connection,
    session_id: str,
    agent_role: str,
    project: str,
    deliverable_type: str,
    title: str,
    content: str,
    downstream_consumers: list[str] | None = None,
    pipeline_id: str | None = None,
) -> int:
    """Save an agent's deliverable for downstream consumption.

    Supersede-on-save: if a deliverable with the same (project, agent_role,
    deliverable_type) already exists and is active, mark it as 'superseded'.

    Args:
        conn: SQLite connection with initialized schema.
        session_id: Current session ID.
        agent_role: The agent that produced this deliverable.
        project: Project name (e.g., 'appendix-k', 'qaqc').
        deliverable_type: Type of deliverable (e.g., 'review', 'architecture').
        title: Short title for the deliverable.
        content: The deliverable content.
        downstream_consumers: Agent roles that should consume this deliverable.
        pipeline_id: Optional pipeline run ID for grouping.

    Returns:
        Deliverable ID.
    """
    # Supersede previous active deliverables with same key
    conn.execute(
        """UPDATE deliverables SET status = 'superseded'
           WHERE project = ? AND agent_role = ? AND deliverable_type = ?
             AND status = 'active'""",
        (project, agent_role, deliverable_type),
    )

    cursor = conn.execute(
        """INSERT INTO deliverables
           (session_id, agent_role, project, deliverable_type, title, content,
            downstream_consumers, pipeline_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            session_id,
            agent_role,
            project,
            deliverable_type,
            title,
            content,
            json.dumps(downstream_consumers) if downstream_consumers else None,
            pipeline_id,
        ),
    )
    conn.commit()
    return cursor.lastrowid  # type: ignore[return-value]


def search_deliverables(
    conn: sqlite3.Connection,
    query: str | None = None,
    project: str | None = None,
    agent_role: str | None = None,
    pipeline_id: str | None = None,
    for_consumer: str | None = None,
    include_archived: bool = False,
    limit: int = 5,
) -> list[dict]:
    """Search deliverables from past agent work.

    Args:
        conn: SQLite connection with initialized schema.
        query: FTS search terms (optional if filtering by other params).
        project: Filter by project name.
        agent_role: Filter by producing agent role.
        pipeline_id: Filter by pipeline run ID.
        for_consumer: Show deliverables tagged for this agent role.
        include_archived: Include archived/superseded deliverables.
        limit: Maximum results.

    Returns:
        List of deliverable dicts sorted by recency.
    """
    conditions: list[str] = []
    params: list = []

    if query:
        safe_query = sanitize_query(query)
        conditions.append(
            "d.id IN (SELECT rowid FROM deliverables_fts WHERE deliverables_fts MATCH ?)"
        )
        params.append(safe_query)

    if project:
        conditions.append("d.project = ?")
        params.append(project)

    if agent_role:
        conditions.append("d.agent_role = ?")
        params.append(agent_role)

    if pipeline_id:
        conditions.append("d.pipeline_id = ?")
        params.append(pipeline_id)

    if for_consumer:
        # Search JSON array for consumer role
        conditions.append("d.downstream_consumers LIKE ?")
        params.append(f'%"{for_consumer}"%')

    if not include_archived:
        conditions.append("d.status = 'active'")
        # Also exclude deliverables older than ARCHIVE_DAYS
        conditions.append(f"d.created_at > datetime('now', '-{ARCHIVE_DAYS} days')")

    where = " AND ".join(conditions) if conditions else "1=1"

    sql = f"""
        SELECT id, session_id, agent_role, project, deliverable_type,
               title, content, downstream_consumers, pipeline_id,
               status, created_at
        FROM deliverables d
        WHERE {where}
        ORDER BY d.created_at DESC
        LIMIT ?
    """
    params.append(limit)

    try:
        rows = conn.execute(sql, params).fetchall()
    except sqlite3.OperationalError:
        return []

    return [
        {
            "id": row["id"],
            "session_id": row["session_id"],
            "agent_role": row["agent_role"],
            "project": row["project"],
            "deliverable_type": row["deliverable_type"],
            "title": row["title"],
            "content": row["content"],
            "downstream_consumers": (
                json.loads(row["downstream_consumers"]) if row["downstream_consumers"] else []
            ),
            "pipeline_id": row["pipeline_id"],
            "status": row["status"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]
