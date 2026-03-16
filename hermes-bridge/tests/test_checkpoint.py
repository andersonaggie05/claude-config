"""Tests for hermes_bridge.checkpoint module."""

from __future__ import annotations

import sqlite3

from hermes_bridge.checkpoint import (
    MAX_SUMMARY_CHARS,
    restore_checkpoint,
    save_checkpoint,
)


class TestSaveCheckpoint:
    def test_basic_save(self, db_conn: sqlite3.Connection) -> None:
        checkpoint_id = save_checkpoint(
            db_conn,
            session_id="s1",
            summary="Working on import parser fix",
            key_decisions=["Use strict validation", "Add dtype enforcement"],
            files_changed=["parser.py", "test_parser.py"],
        )
        assert checkpoint_id is not None
        assert checkpoint_id > 0

    def test_save_without_optional_fields(self, db_conn: sqlite3.Connection) -> None:
        checkpoint_id = save_checkpoint(
            db_conn,
            session_id="s1",
            summary="Simple checkpoint",
        )
        assert checkpoint_id is not None

    def test_summary_truncation(self, db_conn: sqlite3.Connection) -> None:
        long_summary = "x" * (MAX_SUMMARY_CHARS + 100)
        save_checkpoint(db_conn, session_id="s1", summary=long_summary)

        result = restore_checkpoint(db_conn, session_id="s1")
        assert result is not None
        assert len(result["summary"]) == MAX_SUMMARY_CHARS
        assert result["summary"].endswith("...")

    def test_multiple_checkpoints_same_session(self, db_conn: sqlite3.Connection) -> None:
        save_checkpoint(db_conn, session_id="s1", summary="First checkpoint")
        save_checkpoint(db_conn, session_id="s1", summary="Second checkpoint")

        # Restore should return the latest
        result = restore_checkpoint(db_conn, session_id="s1")
        assert result is not None
        assert result["summary"] == "Second checkpoint"


class TestRestoreCheckpoint:
    def test_restore_by_session_id(self, db_conn: sqlite3.Connection) -> None:
        save_checkpoint(
            db_conn,
            session_id="s1",
            summary="Session 1 checkpoint",
            key_decisions=["Decision A"],
            files_changed=["file_a.py"],
        )
        save_checkpoint(
            db_conn,
            session_id="s2",
            summary="Session 2 checkpoint",
        )

        result = restore_checkpoint(db_conn, session_id="s1")
        assert result is not None
        assert result["session_id"] == "s1"
        assert result["summary"] == "Session 1 checkpoint"
        assert result["key_decisions"] == ["Decision A"]
        assert result["files_changed"] == ["file_a.py"]

    def test_restore_latest(self, db_conn: sqlite3.Connection) -> None:
        save_checkpoint(db_conn, session_id="s1", summary="First")
        save_checkpoint(db_conn, session_id="s2", summary="Second")

        result = restore_checkpoint(db_conn)
        assert result is not None
        assert result["summary"] == "Second"

    def test_restore_no_checkpoint(self, db_conn: sqlite3.Connection) -> None:
        result = restore_checkpoint(db_conn, session_id="nonexistent")
        assert result is None

    def test_restore_empty_lists(self, db_conn: sqlite3.Connection) -> None:
        save_checkpoint(db_conn, session_id="s1", summary="test")

        result = restore_checkpoint(db_conn, session_id="s1")
        assert result is not None
        assert result["key_decisions"] == []
        assert result["files_changed"] == []

    def test_restore_has_created_at(self, db_conn: sqlite3.Connection) -> None:
        save_checkpoint(db_conn, session_id="s1", summary="test")

        result = restore_checkpoint(db_conn, session_id="s1")
        assert result is not None
        assert result["created_at"] is not None
