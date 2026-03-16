"""Tests for hermes_bridge.indexer module."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from hermes_bridge.indexer import _extract_text_content, index_session


class TestExtractTextContent:
    def test_plain_string(self) -> None:
        assert _extract_text_content("hello world") == "hello world"

    def test_empty_string(self) -> None:
        assert _extract_text_content("") is None
        assert _extract_text_content("   ") is None

    def test_text_block(self) -> None:
        assert _extract_text_content({"type": "text", "text": "hello"}) == "hello"

    def test_tool_use_block(self) -> None:
        assert _extract_text_content({"type": "tool_use", "id": "t1"}) is None

    def test_thinking_block(self) -> None:
        assert _extract_text_content({"type": "thinking", "thinking": "hmm"}) is None

    def test_list_with_text(self) -> None:
        content = [
            {"type": "text", "text": "first"},
            {"type": "text", "text": "second"},
        ]
        result = _extract_text_content(content)
        assert result == "first\nsecond"

    def test_list_mixed(self) -> None:
        content = [
            {"type": "thinking", "thinking": "hmm"},
            {"type": "text", "text": "visible"},
            {"type": "tool_use", "id": "t1"},
        ]
        result = _extract_text_content(content)
        assert result == "visible"

    def test_list_no_text(self) -> None:
        content = [
            {"type": "tool_result", "tool_use_id": "t1", "content": "output"},
        ]
        assert _extract_text_content(content) is None

    def test_list_empty_text(self) -> None:
        content = [{"type": "text", "text": "   "}]
        assert _extract_text_content(content) is None


class TestIndexSession:
    def test_basic_indexing(self, db_conn: sqlite3.Connection, sample_jsonl: Path) -> None:
        result = index_session(db_conn, sample_jsonl, "test-project")

        assert result["session_id"] == "test-session-001"
        assert result["slug"] == "test-session-slug"
        assert result["message_count"] == 4  # 2 user + 2 assistant text messages
        assert result["tool_use_count"] == 1  # 1 tool_use

    def test_session_metadata(self, db_conn: sqlite3.Connection, sample_jsonl: Path) -> None:
        index_session(db_conn, sample_jsonl, "test-project")

        row = db_conn.execute(
            "SELECT * FROM sessions WHERE session_id = ?", ("test-session-001",)
        ).fetchone()
        assert row["slug"] == "test-session-slug"
        assert row["project"] == "test-project"
        assert row["cwd"] is not None
        assert row["git_branch"] is not None
        assert row["message_count"] == 4
        assert row["tool_use_count"] == 1

    def test_messages_stored(self, db_conn: sqlite3.Connection, sample_jsonl: Path) -> None:
        index_session(db_conn, sample_jsonl, "test-project")

        messages = db_conn.execute(
            "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id",
            ("test-session-001",),
        ).fetchall()

        assert len(messages) == 4
        assert messages[0]["role"] == "user"
        assert "import parser" in messages[0]["content"]
        assert messages[1]["role"] == "assistant"
        assert "dtype validation" in messages[1]["content"]
        assert messages[2]["role"] == "user"
        assert "compliance module" in messages[2]["content"]
        assert messages[3]["role"] == "assistant"
        assert "pandas dtype" in messages[3]["content"]

    def test_fts_searchable(self, db_conn: sqlite3.Connection, sample_jsonl: Path) -> None:
        index_session(db_conn, sample_jsonl, "test-project")

        results = db_conn.execute(
            "SELECT * FROM messages_fts WHERE messages_fts MATCH 'import parser'"
        ).fetchall()
        assert len(results) >= 1

        results = db_conn.execute(
            "SELECT * FROM messages_fts WHERE messages_fts MATCH 'compliance'"
        ).fetchall()
        assert len(results) >= 1

    def test_skips_system_entries(self, db_conn: sqlite3.Connection, sample_jsonl: Path) -> None:
        index_session(db_conn, sample_jsonl, "test-project")

        # No system messages should be stored
        results = db_conn.execute(
            "SELECT * FROM messages_fts WHERE messages_fts MATCH 'stop_hook_summary'"
        ).fetchall()
        assert len(results) == 0

    def test_skips_thinking_blocks(self, db_conn: sqlite3.Connection, sample_jsonl: Path) -> None:
        index_session(db_conn, sample_jsonl, "test-project")

        results = db_conn.execute(
            "SELECT * FROM messages_fts WHERE messages_fts MATCH 'analyze'"
        ).fetchall()
        assert len(results) == 0

    def test_streaming_deduplication(
        self, db_conn: sqlite3.Connection, sample_jsonl_streaming: Path
    ) -> None:
        result = index_session(db_conn, sample_jsonl_streaming, "test-project")

        # Two streaming chunks with same requestId should become 1 message
        assert result["message_count"] == 2  # 1 user + 1 deduplicated assistant

        messages = db_conn.execute(
            "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id",
            ("test-session-streaming",),
        ).fetchall()
        assert len(messages) == 2
        assert messages[1]["role"] == "assistant"
        assert "compression works by" in messages[1]["content"]
        assert "preserving head and tail" in messages[1]["content"]

    def test_reindex_overwrites(self, db_conn: sqlite3.Connection, sample_jsonl: Path) -> None:
        # Index twice
        index_session(db_conn, sample_jsonl, "test-project")
        result = index_session(db_conn, sample_jsonl, "test-project")

        # Should not duplicate messages
        count = db_conn.execute(
            "SELECT COUNT(*) FROM messages WHERE session_id = ?",
            ("test-session-001",),
        ).fetchone()[0]
        assert count == result["message_count"]

    def test_no_session_id_raises(self, db_conn: sqlite3.Connection, tmp_path: Path) -> None:
        # JSONL with no sessionId
        jsonl_path = tmp_path / "empty.jsonl"
        jsonl_path.write_text('{"type": "system", "subtype": "test"}\n')

        with pytest.raises(ValueError, match="No sessionId"):
            index_session(db_conn, jsonl_path, "test-project")
