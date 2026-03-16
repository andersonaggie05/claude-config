"""Tests for hermes_bridge.search module."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from hermes_bridge.indexer import index_session
from hermes_bridge.search import sanitize_query, search_sessions


class TestSanitizeQuery:
    def test_plain_text(self) -> None:
        assert sanitize_query("hello world") == "hello world"

    def test_removes_backticks(self) -> None:
        assert sanitize_query("`import parser`") == "import parser"

    def test_removes_unmatched_close_paren(self) -> None:
        assert sanitize_query("test)") == "test"

    def test_removes_unmatched_open_paren(self) -> None:
        assert sanitize_query("(test") == "test"

    def test_preserves_matched_parens(self) -> None:
        assert sanitize_query("(test)") == "(test)"

    def test_collapses_spaces(self) -> None:
        assert sanitize_query("hello   world") == "hello world"

    def test_empty_returns_empty_quotes(self) -> None:
        assert sanitize_query("") == '""'
        assert sanitize_query("```") == '""'

    def test_complex_query(self) -> None:
        result = sanitize_query("`import` parser (validation)")
        assert "import" in result
        assert "parser" in result


class TestSearchSessions:
    def test_basic_search(self, db_conn: sqlite3.Connection, sample_jsonl: Path) -> None:
        index_session(db_conn, sample_jsonl, "test-project")

        results = search_sessions(db_conn, "import parser")
        assert len(results) >= 1
        assert results[0]["session_id"] == "test-session-001"
        assert results[0]["project"] == "test-project"
        assert len(results[0]["matched_messages"]) >= 1

    def test_search_with_project_filter(
        self, db_conn: sqlite3.Connection, sample_jsonl: Path
    ) -> None:
        index_session(db_conn, sample_jsonl, "test-project")

        # Matching project
        results = search_sessions(db_conn, "import parser", project="test-project")
        assert len(results) >= 1

        # Non-matching project
        results = search_sessions(db_conn, "import parser", project="other-project")
        assert len(results) == 0

    def test_search_returns_snippets(self, db_conn: sqlite3.Connection, sample_jsonl: Path) -> None:
        index_session(db_conn, sample_jsonl, "test-project")

        results = search_sessions(db_conn, "compliance")
        assert len(results) >= 1
        snippets = results[0]["matched_messages"]
        assert len(snippets) >= 1
        # Snippets should contain the highlight markers
        assert any(">>>" in s["snippet"] for s in snippets)

    def test_search_no_results(self, db_conn: sqlite3.Connection, sample_jsonl: Path) -> None:
        index_session(db_conn, sample_jsonl, "test-project")

        results = search_sessions(db_conn, "nonexistent_search_term_xyz")
        assert len(results) == 0

    def test_search_includes_session_metadata(
        self, db_conn: sqlite3.Connection, sample_jsonl: Path
    ) -> None:
        index_session(db_conn, sample_jsonl, "test-project")

        results = search_sessions(db_conn, "dtype")
        assert len(results) >= 1
        session = results[0]
        assert session["slug"] == "test-session-slug"
        assert session["started_at"] is not None
        assert session["message_count"] == 4

    def test_search_limit(
        self, db_conn: sqlite3.Connection, sample_jsonl: Path, sample_jsonl_streaming: Path
    ) -> None:
        index_session(db_conn, sample_jsonl, "test-project")
        index_session(db_conn, sample_jsonl_streaming, "test-project")

        # Both sessions have content; limit=1 should return at most 1
        results = search_sessions(db_conn, "test", limit=1)
        assert len(results) <= 1

    def test_search_with_bad_query(self, db_conn: sqlite3.Connection, sample_jsonl: Path) -> None:
        index_session(db_conn, sample_jsonl, "test-project")

        # Should not raise, just return empty or partial results
        results = search_sessions(db_conn, "```invalid query```")
        assert isinstance(results, list)
