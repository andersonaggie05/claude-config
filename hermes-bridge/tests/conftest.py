"""Shared fixtures for hermes-bridge tests."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from hermes_bridge.db import get_connection, init_db


@pytest.fixture
def db_conn(tmp_path: Path) -> sqlite3.Connection:
    """Provide a fresh SQLite connection with initialized schema."""
    db_path = tmp_path / "test.db"
    conn = get_connection(db_path)
    init_db(conn)
    yield conn
    conn.close()


@pytest.fixture
def sample_jsonl(tmp_path: Path) -> Path:
    """Create a sample JSONL file mimicking Claude Code session format."""
    session_id = "test-session-001"
    entries = [
        # System entry (should be skipped)
        {
            "type": "system",
            "subtype": "stop_hook_summary",
            "timestamp": "2026-03-10T10:00:00.000Z",
            "sessionId": session_id,
            "cwd": "C:\\Users\\Test",
            "gitBranch": "main",
        },
        # Progress entry (should be skipped)
        {
            "type": "progress",
            "data": {"type": "hook_progress"},
            "timestamp": "2026-03-10T10:00:01.000Z",
            "sessionId": session_id,
        },
        # User message (plain text content)
        {
            "type": "user",
            "message": {
                "role": "user",
                "content": "How do I fix the import parser validation?",
            },
            "timestamp": "2026-03-10T10:00:02.000Z",
            "sessionId": session_id,
            "slug": "test-session-slug",
            "cwd": "C:\\Users\\Test\\project",
            "gitBranch": "feature/import-fix",
        },
        # Assistant thinking (should be skipped)
        {
            "type": "assistant",
            "message": {
                "role": "assistant",
                "content": [{"type": "thinking", "thinking": "Let me analyze..."}],
            },
            "requestId": "req_001",
            "timestamp": "2026-03-10T10:00:03.000Z",
            "sessionId": session_id,
        },
        # Assistant text response (first chunk)
        {
            "type": "assistant",
            "message": {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "The import parser has a bug in the dtype validation."}
                ],
            },
            "requestId": "req_001",
            "timestamp": "2026-03-10T10:00:04.000Z",
            "sessionId": session_id,
            "slug": "test-session-slug",
        },
        # Assistant tool_use (should count but not index text)
        {
            "type": "assistant",
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_001",
                        "name": "Read",
                        "input": {"file_path": "/test/file.py"},
                    }
                ],
            },
            "requestId": "req_002",
            "timestamp": "2026-03-10T10:00:05.000Z",
            "sessionId": session_id,
        },
        # User tool_result (should be skipped - no text)
        {
            "type": "user",
            "message": {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": "toolu_001",
                        "content": "file contents here...",
                    }
                ],
            },
            "timestamp": "2026-03-10T10:00:06.000Z",
            "sessionId": session_id,
        },
        # User message with array content containing text
        {
            "type": "user",
            "message": {
                "role": "user",
                "content": [{"type": "text", "text": "Can you also check the compliance module?"}],
            },
            "timestamp": "2026-03-10T10:00:07.000Z",
            "sessionId": session_id,
        },
        # Assistant response
        {
            "type": "assistant",
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": "The compliance module uses strict validation "
                        "with pandas dtype enforcement.",
                    }
                ],
            },
            "requestId": "req_003",
            "timestamp": "2026-03-10T10:00:08.000Z",
            "sessionId": session_id,
        },
        # File history snapshot (should be skipped)
        {
            "type": "file-history-snapshot",
            "messageId": "msg_001",
            "snapshot": {},
        },
    ]

    jsonl_path = tmp_path / f"{session_id}.jsonl"
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")

    return jsonl_path


@pytest.fixture
def sample_jsonl_streaming(tmp_path: Path) -> Path:
    """Create a JSONL file with streaming assistant chunks (same requestId)."""
    session_id = "test-session-streaming"
    entries = [
        {
            "type": "user",
            "message": {"role": "user", "content": "Explain context compression"},
            "timestamp": "2026-03-10T11:00:00.000Z",
            "sessionId": session_id,
            "cwd": "C:\\Users\\Test",
        },
        # First streaming chunk
        {
            "type": "assistant",
            "message": {
                "role": "assistant",
                "content": [{"type": "text", "text": "Context compression works by"}],
            },
            "requestId": "req_stream_001",
            "timestamp": "2026-03-10T11:00:01.000Z",
            "sessionId": session_id,
        },
        # Second streaming chunk (same requestId)
        {
            "type": "assistant",
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": "summarizing middle turns while preserving head and tail.",
                    }
                ],
            },
            "requestId": "req_stream_001",
            "timestamp": "2026-03-10T11:00:02.000Z",
            "sessionId": session_id,
        },
    ]

    jsonl_path = tmp_path / f"{session_id}.jsonl"
    with open(jsonl_path, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")

    return jsonl_path
