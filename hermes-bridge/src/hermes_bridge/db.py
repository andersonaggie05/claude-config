"""SQLite database management with FTS5 for hermes-bridge."""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA_VERSION = 2

DEFAULT_DB_PATH = Path.home() / ".claude" / "hermes-bridge" / "data" / "bridge.db"

SCHEMA_SQL = """\
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    slug TEXT,
    project TEXT NOT NULL,
    started_at TEXT,
    ended_at TEXT,
    cwd TEXT,
    git_branch TEXT,
    message_count INTEGER DEFAULT 0,
    tool_use_count INTEGER DEFAULT 0,
    summary TEXT,
    indexed_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    timestamp TEXT
);

CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);

CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
    content,
    content=messages,
    content_rowid=id,
    tokenize='porter unicode61'
);

CREATE TABLE IF NOT EXISTS checkpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    summary TEXT NOT NULL,
    key_decisions TEXT,
    files_changed TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
"""

FTS_TRIGGERS_SQL = """\
CREATE TRIGGER IF NOT EXISTS messages_fts_insert AFTER INSERT ON messages BEGIN
    INSERT INTO messages_fts(rowid, content) VALUES (new.id, new.content);
END;

CREATE TRIGGER IF NOT EXISTS messages_fts_delete AFTER DELETE ON messages BEGIN
    INSERT INTO messages_fts(messages_fts, rowid, content) VALUES('delete', old.id, old.content);
END;

CREATE TRIGGER IF NOT EXISTS messages_fts_update AFTER UPDATE ON messages BEGIN
    INSERT INTO messages_fts(messages_fts, rowid, content) VALUES('delete', old.id, old.content);
    INSERT INTO messages_fts(rowid, content) VALUES (new.id, new.content);
END;
"""


SCHEMA_V2_SQL = """\
CREATE TABLE IF NOT EXISTS deliverables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    agent_role TEXT NOT NULL,
    project TEXT NOT NULL,
    deliverable_type TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    downstream_consumers TEXT,
    pipeline_id TEXT,
    status TEXT DEFAULT 'active',
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_deliverables_project ON deliverables(project);
CREATE INDEX IF NOT EXISTS idx_deliverables_agent ON deliverables(agent_role);
CREATE INDEX IF NOT EXISTS idx_deliverables_pipeline ON deliverables(pipeline_id);
CREATE INDEX IF NOT EXISTS idx_deliverables_status ON deliverables(status);

CREATE VIRTUAL TABLE IF NOT EXISTS deliverables_fts USING fts5(
    title,
    content,
    content=deliverables,
    content_rowid=id,
    tokenize='porter unicode61'
);

CREATE TRIGGER IF NOT EXISTS deliverables_fts_insert AFTER INSERT ON deliverables BEGIN
    INSERT INTO deliverables_fts(rowid, title, content) VALUES (new.id, new.title, new.content);
END;

CREATE TRIGGER IF NOT EXISTS deliverables_fts_delete AFTER DELETE ON deliverables BEGIN
    INSERT INTO deliverables_fts(deliverables_fts, rowid, title, content)
        VALUES('delete', old.id, old.title, old.content);
END;

CREATE TRIGGER IF NOT EXISTS deliverables_fts_update AFTER UPDATE ON deliverables BEGIN
    INSERT INTO deliverables_fts(deliverables_fts, rowid, title, content)
        VALUES('delete', old.id, old.title, old.content);
    INSERT INTO deliverables_fts(rowid, title, content) VALUES (new.id, new.title, new.content);
END;
"""

ARCHIVE_DAYS = 90


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """Create a SQLite connection with WAL mode and recommended settings."""
    path = db_path or DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(path), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """Initialize the database schema if needed, applying incremental migrations."""
    # Check current version
    try:
        row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
        current_version = row[0] if row[0] is not None else 0
    except sqlite3.OperationalError:
        current_version = 0

    if current_version >= SCHEMA_VERSION:
        return

    # Apply v1 base schema (idempotent via CREATE IF NOT EXISTS)
    if current_version < 1:
        conn.executescript(SCHEMA_SQL)
        conn.executescript(FTS_TRIGGERS_SQL)

    # Apply v2 migration: deliverables table + FTS
    if current_version < 2:
        conn.executescript(SCHEMA_V2_SQL)

    conn.execute(
        "INSERT OR REPLACE INTO schema_version (version) VALUES (?)",
        (SCHEMA_VERSION,),
    )
    conn.commit()


def reset_db(conn: sqlite3.Connection) -> None:
    """Drop and recreate all tables. Used in tests."""
    conn.executescript("""
        DROP TABLE IF EXISTS deliverables;
        DROP TABLE IF EXISTS deliverables_fts;
        DROP TABLE IF EXISTS checkpoints;
        DROP TABLE IF EXISTS messages;
        DROP TABLE IF EXISTS messages_fts;
        DROP TABLE IF EXISTS sessions;
        DROP TABLE IF EXISTS schema_version;
    """)
    # Drop triggers (they reference tables that were just dropped)
    for trigger in (
        "messages_fts_insert",
        "messages_fts_delete",
        "messages_fts_update",
        "deliverables_fts_insert",
        "deliverables_fts_delete",
        "deliverables_fts_update",
    ):
        conn.execute(f"DROP TRIGGER IF EXISTS {trigger}")
    conn.commit()
    init_db(conn)
