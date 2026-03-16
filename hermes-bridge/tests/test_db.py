"""Tests for hermes_bridge.db module."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from hermes_bridge.db import SCHEMA_VERSION, get_connection, init_db, reset_db


def test_get_connection_creates_db(tmp_path: Path) -> None:
    db_path = tmp_path / "subdir" / "test.db"
    conn = get_connection(db_path)
    assert db_path.exists()
    # Verify WAL mode
    mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
    assert mode == "wal"
    conn.close()


def test_init_db_creates_tables(db_conn: sqlite3.Connection) -> None:
    tables = {
        row[0]
        for row in db_conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    }
    assert "sessions" in tables
    assert "messages" in tables
    assert "checkpoints" in tables
    assert "schema_version" in tables


def test_init_db_creates_fts(db_conn: sqlite3.Connection) -> None:
    tables = {
        row[0]
        for row in db_conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    }
    assert "messages_fts" in tables


def test_init_db_creates_triggers(db_conn: sqlite3.Connection) -> None:
    triggers = {
        row[0]
        for row in db_conn.execute("SELECT name FROM sqlite_master WHERE type='trigger'").fetchall()
    }
    assert "messages_fts_insert" in triggers
    assert "messages_fts_delete" in triggers
    assert "messages_fts_update" in triggers


def test_init_db_idempotent(db_conn: sqlite3.Connection) -> None:
    # Calling init_db again should not fail
    init_db(db_conn)
    version = db_conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
    assert version == SCHEMA_VERSION


def test_schema_version_recorded(db_conn: sqlite3.Connection) -> None:
    version = db_conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
    assert version == SCHEMA_VERSION


def test_fts_trigger_insert(db_conn: sqlite3.Connection) -> None:
    # Insert a session first (FK constraint)
    db_conn.execute(
        "INSERT INTO sessions (session_id, project) VALUES (?, ?)",
        ("s1", "test-project"),
    )
    db_conn.execute(
        "INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
        ("s1", "user", "hello world test message", "2026-01-01T00:00:00Z"),
    )
    db_conn.commit()

    # FTS should find it
    results = db_conn.execute(
        "SELECT * FROM messages_fts WHERE messages_fts MATCH 'hello'"
    ).fetchall()
    assert len(results) == 1


def test_fts_trigger_delete(db_conn: sqlite3.Connection) -> None:
    db_conn.execute(
        "INSERT INTO sessions (session_id, project) VALUES (?, ?)",
        ("s1", "test-project"),
    )
    db_conn.execute(
        "INSERT INTO messages (session_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
        ("s1", "user", "unique_test_word_xyz", "2026-01-01T00:00:00Z"),
    )
    db_conn.commit()

    # Delete the message
    db_conn.execute("DELETE FROM messages WHERE session_id = 's1'")
    db_conn.commit()

    # FTS should no longer find it
    results = db_conn.execute(
        "SELECT * FROM messages_fts WHERE messages_fts MATCH 'unique_test_word_xyz'"
    ).fetchall()
    assert len(results) == 0


def test_reset_db(db_conn: sqlite3.Connection) -> None:
    db_conn.execute(
        "INSERT INTO sessions (session_id, project) VALUES (?, ?)",
        ("s1", "test-project"),
    )
    db_conn.commit()

    reset_db(db_conn)

    count = db_conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
    assert count == 0

    version = db_conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
    assert version == SCHEMA_VERSION


def test_foreign_key_cascade(db_conn: sqlite3.Connection) -> None:
    db_conn.execute(
        "INSERT INTO sessions (session_id, project) VALUES (?, ?)",
        ("s1", "test-project"),
    )
    db_conn.execute(
        "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
        ("s1", "user", "test message"),
    )
    db_conn.commit()

    # Delete session should cascade to messages
    db_conn.execute("DELETE FROM sessions WHERE session_id = 's1'")
    db_conn.commit()

    count = db_conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    assert count == 0
