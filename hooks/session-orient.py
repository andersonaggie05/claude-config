"""SessionStart hook: orient phase — inject context from hermes-bridge and vault.

Fires on every session start (no matcher). Queries hermes-bridge for recent
session context and qmd for relevant vault knowledge based on the current project.
Graceful degradation: if either source fails, returns whatever is available.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# hermes-bridge imports
sys.path.insert(0, str(Path.home() / ".claude" / "hermes-bridge" / "src"))

from hermes_bridge.db import get_connection, init_db

LOG_DIR = Path.home() / ".claude" / "hermes-bridge" / "data"
LOG_FILE = LOG_DIR / "hooks.log"

MAX_CONTEXT_CHARS = 3000  # ~750 tokens

# Full path to qmd JS entry — npm .cmd wrappers don't work from Python subprocess
QMD_JS = Path.home() / "AppData" / "Roaming" / "npm" / "node_modules" / "@tobilu" / "qmd" / "dist" / "cli" / "qmd.js"


def log(msg: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now(timezone.utc).isoformat()}] session-orient: {msg}\n")


def derive_project_slug(cwd: str) -> str:
    """Derive hermes-bridge project slug from cwd path.

    hermes-bridge stores projects as path slugs like 'C--Users-Anderfail-appendix-k'.
    """
    # Normalize path separators and convert to slug format
    normalized = cwd.replace("\\", "/").replace(":", "").strip("/")
    return normalized.replace("/", "-")


def derive_project_name(cwd: str) -> str:
    """Derive human-readable project name from cwd for vault search."""
    path = Path(cwd)
    name = path.name or "unknown"
    # Convert common separators to spaces for better search
    return name.replace("-", " ").replace("_", " ")


def query_hermes(project: str) -> str:
    """Query hermes-bridge for recent session summaries for this project."""
    try:
        conn = get_connection()
        init_db(conn)
        rows = conn.execute(
            """SELECT session_id, summary, ended_at
               FROM sessions
               WHERE project = ? AND summary IS NOT NULL
               ORDER BY ended_at DESC
               LIMIT 3""",
            (project,),
        ).fetchall()
        conn.close()

        if not rows:
            return ""

        parts = ["Recent sessions:"]
        for row in rows:
            ended = row["ended_at"] or "unknown"
            summary = row["summary"] or "(no summary)"
            # Truncate individual summaries
            if len(summary) > 500:
                summary = summary[:500] + "..."
            parts.append(f"  [{ended}] {summary}")

        return "\n".join(parts)
    except Exception as e:
        log(f"hermes-bridge query failed: {e}")
        return ""


def query_vault(project: str) -> str:
    """Query qmd for relevant vault knowledge based on project name."""
    try:
        if not QMD_JS.exists():
            log(f"qmd.js not found at {QMD_JS}")
            return ""
        result = subprocess.run(
            ["node", str(QMD_JS), "search", project, "--json", "-n", "3"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            log(f"qmd search failed: {result.stderr[:200]}")
            return ""

        data = json.loads(result.stdout)
        if not data:
            return ""

        parts = ["Relevant vault knowledge:"]
        for item in data[:3]:
            title = item.get("title", item.get("path", "untitled"))
            snippet = item.get("snippet", item.get("content", ""))
            if len(snippet) > 300:
                snippet = snippet[:300] + "..."
            parts.append(f"  [{title}] {snippet}")

        return "\n".join(parts)
    except subprocess.TimeoutExpired:
        log("qmd search timed out (10s)")
        return ""
    except FileNotFoundError:
        log("qmd not found in PATH")
        return ""
    except Exception as e:
        log(f"qmd query failed: {e}")
        return ""


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception as e:
        log(f"ERROR reading stdin: {e}")
        return

    cwd = payload.get("cwd", "")
    project_slug = derive_project_slug(cwd)
    project_name = derive_project_name(cwd)

    # Query both sources
    hermes_context = query_hermes(project_slug)
    vault_context = query_vault(project_name)

    if not hermes_context and not vault_context:
        log(f"No context found for project '{project_name}' (slug: {project_slug})")
        return

    # Combine and truncate
    parts = [f"[SESSION ORIENTATION] Project: {project_name}"]
    if hermes_context:
        parts.append(hermes_context)
    if vault_context:
        parts.append(vault_context)

    context = "\n\n".join(parts)
    if len(context) > MAX_CONTEXT_CHARS:
        context = context[:MAX_CONTEXT_CHARS] + "\n... (truncated)"

    result = {
        "hookSpecificOutput": {
            "additionalContext": context,
        }
    }
    json.dump(result, sys.stdout)
    log(f"Injected orient context for '{project_name}' ({len(context)} chars)")


if __name__ == "__main__":
    main()
