"""Backfill script: indexes all existing JSONL session files into hermes-bridge."""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from hermes_bridge.db import get_connection, init_db
from hermes_bridge.indexer import index_session

PROJECTS_DIR = Path.home() / ".claude" / "projects"
UUID_PATTERN = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.jsonl$")


def find_session_files() -> list[tuple[Path, str]]:
    """Find all top-level JSONL session files (skip subagents/)."""
    results = []
    if not PROJECTS_DIR.exists():
        return results

    for project_dir in PROJECTS_DIR.iterdir():
        if not project_dir.is_dir():
            continue
        project_name = project_dir.name

        for jsonl_file in project_dir.glob("*.jsonl"):
            # Only UUID-named files (skip subagent files)
            if UUID_PATTERN.match(jsonl_file.name):
                results.append((jsonl_file, project_name))

    return results


def main() -> None:
    conn = get_connection()
    init_db(conn)

    files = find_session_files()
    print(f"Found {len(files)} session files to index")

    indexed = 0
    errors = 0
    for jsonl_path, project in files:
        try:
            result = index_session(conn, jsonl_path, project)
            indexed += 1
            print(
                f"  [{indexed}/{len(files)}] {result['session_id'][:8]}... "
                f"({result['message_count']} msgs, slug={result.get('slug')})"
            )
        except Exception as e:
            errors += 1
            print(f"  ERROR {jsonl_path.name}: {e}")

    conn.close()
    print(f"\nDone: {indexed} indexed, {errors} errors, {len(files)} total")


if __name__ == "__main__":
    main()
