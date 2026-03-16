"""MCP server for hermes-bridge: session search, indexing, and checkpointing."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from hermes_bridge.checkpoint import restore_checkpoint, save_checkpoint
from hermes_bridge.db import DEFAULT_DB_PATH, get_connection, init_db
from hermes_bridge.deliverables import save_deliverable, search_deliverables
from hermes_bridge.indexer import index_session
from hermes_bridge.search import search_sessions

logger = logging.getLogger(__name__)

mcp = FastMCP(
    "hermes-bridge",
    instructions=(
        "Cross-session search, context checkpointing, and session indexing for Claude Code. "
        "Use session_search to find information from past conversations. "
        "Use checkpoint_save before context compaction to preserve state. "
        "Use checkpoint_restore after compaction to recover context. "
        "Use deliverable_save to store agent outputs for downstream agent consumption. "
        "Use deliverable_search to find deliverables from past agent work."
    ),
)


def _get_conn():
    """Get a database connection, initializing schema if needed."""
    conn = get_connection(DEFAULT_DB_PATH)
    init_db(conn)
    return conn


@mcp.tool()
def session_search(query: str, project: str | None = None, limit: int = 5) -> str:
    """Search past Claude Code sessions using full-text search.

    Use this when the user references past work, asks about previous conversations,
    or when you need to recover context from earlier sessions.

    Args:
        query: Search terms (supports phrases in quotes, OR/AND operators).
        project: Optional project name to filter results (e.g., "C--Users-Anderfail-appendix-k").
        limit: Maximum number of sessions to return (default 5).

    Returns:
        JSON array of matching sessions with message snippets.
    """
    conn = _get_conn()
    try:
        results = search_sessions(conn, query, project=project, limit=limit)
        return json.dumps(results, indent=2)
    finally:
        conn.close()


@mcp.tool()
def session_index(session_id: str, jsonl_path: str) -> str:
    """Index a Claude Code session transcript for future search.

    Typically called by the SessionEnd hook automatically, but can also be used
    to manually index or re-index a session.

    Args:
        session_id: The session UUID.
        jsonl_path: Absolute path to the .jsonl transcript file.

    Returns:
        JSON object with indexing stats.
    """
    path = Path(jsonl_path)
    if not path.exists():
        return json.dumps({"error": f"File not found: {jsonl_path}"})

    # Derive project name from the path
    # Pattern: ~/.claude/projects/<project-name>/<session-id>.jsonl
    project = path.parent.name

    conn = _get_conn()
    try:
        result = index_session(conn, path, project)
        return json.dumps({"status": "indexed", **result})
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        conn.close()


@mcp.tool()
def checkpoint_save(
    session_id: str,
    summary: str,
    key_decisions: list[str] | None = None,
    files_changed: list[str] | None = None,
) -> str:
    """Save a context checkpoint before compaction.

    Called by the PreCompact hook or manually when you want to preserve
    the current conversation state.

    Args:
        session_id: Current session UUID.
        summary: Summary of conversation state (max 2000 chars).
        key_decisions: List of key decisions made in this session.
        files_changed: List of files modified in this session.

    Returns:
        JSON object with checkpoint ID.
    """
    conn = _get_conn()
    try:
        checkpoint_id = save_checkpoint(
            conn,
            session_id,
            summary,
            key_decisions=key_decisions,
            files_changed=files_changed,
        )
        return json.dumps({"status": "saved", "checkpoint_id": checkpoint_id})
    finally:
        conn.close()


@mcp.tool()
def checkpoint_restore(session_id: str | None = None) -> str:
    """Restore the latest context checkpoint for a session.

    Use after context compaction to recover conversation state, or at the
    start of a new session to continue previous work.

    Args:
        session_id: Session UUID to restore from. If omitted, returns the most recent checkpoint.

    Returns:
        JSON object with checkpoint data, or error if no checkpoint found.
    """
    conn = _get_conn()
    try:
        result = restore_checkpoint(conn, session_id=session_id)
        if result is None:
            return json.dumps({"error": "No checkpoint found"})
        return json.dumps(result, indent=2)
    finally:
        conn.close()


@mcp.tool()
def deliverable_save(
    session_id: str,
    agent_role: str,
    project: str,
    deliverable_type: str,
    title: str,
    content: str,
    downstream_consumers: list[str] | None = None,
    pipeline_id: str | None = None,
) -> str:
    """Save an agent's deliverable for downstream consumption.

    Use this when an agent completes a task and produces output that
    other agents need to consume (reviews, architecture docs, assessments).
    Automatically supersedes previous deliverables with the same
    (project, agent_role, deliverable_type).

    Args:
        session_id: Current session UUID.
        agent_role: The agent that produced this (e.g., 'reality-checker').
        project: Project name (e.g., 'appendix-k', 'qaqc').
        deliverable_type: Type (e.g., 'review', 'architecture', 'sprint-plan').
        title: Short title for the deliverable.
        content: The deliverable content.
        downstream_consumers: Agent roles that should see this.
        pipeline_id: Optional pipeline run ID for grouping.

    Returns:
        JSON object with deliverable ID.
    """
    conn = _get_conn()
    try:
        deliverable_id = save_deliverable(
            conn,
            session_id,
            agent_role,
            project,
            deliverable_type,
            title,
            content,
            downstream_consumers=downstream_consumers,
            pipeline_id=pipeline_id,
        )
        return json.dumps({"status": "saved", "deliverable_id": deliverable_id})
    finally:
        conn.close()


@mcp.tool()
def deliverable_search(
    query: str | None = None,
    project: str | None = None,
    agent_role: str | None = None,
    pipeline_id: str | None = None,
    for_consumer: str | None = None,
    include_archived: bool = False,
    limit: int = 5,
) -> str:
    """Search deliverables from past agent work.

    Use this when an agent needs context from a previous agent's output,
    or when resuming a pipeline across sessions.

    Args:
        query: FTS search terms (optional if filtering by other params).
        project: Filter by project name.
        agent_role: Filter by producing agent role.
        pipeline_id: Filter by pipeline run ID.
        for_consumer: Show deliverables tagged for this agent role.
        include_archived: Include archived/superseded deliverables (default False).
        limit: Maximum results (default 5).

    Returns:
        JSON array of matching deliverables.
    """
    conn = _get_conn()
    try:
        results = search_deliverables(
            conn,
            query=query,
            project=project,
            agent_role=agent_role,
            pipeline_id=pipeline_id,
            for_consumer=for_consumer,
            include_archived=include_archived,
            limit=limit,
        )
        return json.dumps(results, indent=2)
    finally:
        conn.close()


def main() -> None:
    """Run the MCP server via stdio transport."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
