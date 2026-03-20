#!/usr/bin/env python3
"""SessionEnd hook: extract knowledge candidates from transcript into vault inbox.

Scans the session transcript for:
1. Retrospective content (Layer 1/2/3 markers)
2. Decisions and rationale (with any subsequent corrections)
3. User corrections (feedback signals)

Creates draft inbox notes in ~/vault/inbox/ for later triage via /vault-review.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

VAULT_INBOX = Path.home() / "vault" / "inbox"
LOG_DIR = Path.home() / ".claude" / "hermes-bridge" / "data"
LOG_FILE = LOG_DIR / "hooks.log"

MIN_MESSAGES = 10  # Skip short sessions

# --- Extraction patterns ---

RETRO_MARKERS = [
    "Layer 1: Work Review",
    "Layer 2: Process Review",
    "Layer 3: System Evolution",
    "## Work Review",
    "## Process Review",
    "## System Evolution",
]

DECISION_PATTERNS = [
    re.compile(r"(?i)\bdecided to\b"),
    re.compile(r"(?i)\bchose .+ over\b"),
    re.compile(r"(?i)\bthe approach is\b"),
    re.compile(r"(?i)\btrade-off:"),
    re.compile(r"(?i)\bwent with\b"),
    re.compile(r"(?i)\bbetter approach\b"),
    re.compile(r"(?i)\bADR\b"),
    re.compile(r"(?i)\barchitecture decision\b"),
]

CORRECTION_PATTERNS = [
    re.compile(r"(?i)^no[,.\s]"),
    re.compile(r"(?i)\bdon'?t do that\b"),
    re.compile(r"(?i)^stop\b"),
    re.compile(r"(?i)\binstead\b"),
    re.compile(r"(?i)\bnot that way\b"),
    re.compile(r"(?i)\bwrong\b"),
    re.compile(r"(?i)\bthat'?s not\b"),
    re.compile(r"(?i)^actually[,]\s"),
]

# Max chars per extracted section to avoid huge inbox notes
MAX_SECTION_CHARS = 3000


def log(msg: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(
            f"[{datetime.now(timezone.utc).isoformat()}] session-extract: {msg}\n"
        )


def extract_text_content(content: str | list | dict) -> str | None:
    """Extract plain text from a message content field.

    Mirrors hermes_bridge.indexer._extract_text_content.
    """
    if isinstance(content, str):
        return content if content.strip() else None

    if isinstance(content, dict):
        if content.get("type") == "text":
            return content.get("text", "")
        return None

    if isinstance(content, list):
        text_parts = []
        for block in content:
            if isinstance(block, str):
                text_parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                text = block.get("text", "")
                if text.strip():
                    text_parts.append(text)
        return "\n".join(text_parts) if text_parts else None

    return None


def parse_transcript(
    path: Path,
) -> tuple[list[dict], str | None, str | None, str | None]:
    """Parse transcript JSONL into messages list and metadata.

    Returns (messages, session_id, slug, project) where messages is a list of
    {role, content, index} dicts with deduplicated assistant streaming chunks.
    """
    session_id: str | None = None
    slug: str | None = None
    cwd: str | None = None

    messages: list[dict] = []
    seen_request_ids: dict[str, int] = {}

    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            if session_id is None:
                session_id = entry.get("sessionId")
            if entry.get("slug"):
                slug = entry["slug"]
            if cwd is None:
                cwd = entry.get("cwd")

            entry_type = entry.get("type")
            if entry_type in ("system", "progress", "file-history-snapshot"):
                continue

            message = entry.get("message", {})
            role = message.get("role")
            if role not in ("user", "assistant"):
                continue

            content = message.get("content")
            if content is None:
                continue

            text = extract_text_content(content)
            if not text or not text.strip():
                continue

            request_id = entry.get("requestId")
            if role == "assistant" and request_id and request_id in seen_request_ids:
                idx = seen_request_ids[request_id]
                messages[idx]["content"] += "\n" + text
            else:
                idx = len(messages)
                messages.append({"role": role, "content": text, "index": idx})
                if role == "assistant" and request_id:
                    seen_request_ids[request_id] = idx

    project = Path(cwd).name if cwd else path.parent.name

    return messages, session_id, slug, project


def extract_retrospective(messages: list[dict]) -> str | None:
    """Extract retrospective content if Layer 1/2/3 markers are found."""
    retro_lines: list[str] = []
    capturing = False

    for msg in messages:
        if msg["role"] != "assistant":
            continue
        content = msg["content"]

        if any(marker in content for marker in RETRO_MARKERS):
            capturing = True

        if capturing:
            retro_lines.append(content)

    if not retro_lines:
        return None

    text = "\n\n".join(retro_lines)
    if len(text) > MAX_SECTION_CHARS:
        text = text[:MAX_SECTION_CHARS] + "\n\n... (truncated)"
    return text


def extract_decisions(messages: list[dict]) -> str | None:
    """Extract decision-related messages with surrounding context.

    If a user correction follows a decision within 5 messages, includes
    the correction alongside the decision to preserve full context.
    """
    decision_blocks: list[str] = []
    seen_indices: set[int] = set()

    for i, msg in enumerate(messages):
        if msg["role"] != "assistant":
            continue

        if any(p.search(msg["content"]) for p in DECISION_PATTERNS):
            if i in seen_indices:
                continue

            block_parts: list[str] = []

            # Include 1 message before for context
            if i > 0:
                prev = messages[i - 1]
                block_parts.append(f"**{prev['role'].title()}:** {prev['content']}")
                seen_indices.add(i - 1)

            block_parts.append(f"**Assistant:** {msg['content']}")
            seen_indices.add(i)

            # Check next 5 messages for corrections
            for j in range(i + 1, min(i + 6, len(messages))):
                following = messages[j]
                if following["role"] == "user" and any(
                    p.search(following["content"]) for p in CORRECTION_PATTERNS
                ):
                    block_parts.append(
                        f"**User (correction):** {following['content']}"
                    )
                    seen_indices.add(j)
                    # Also include the assistant response to the correction
                    if j + 1 < len(messages) and messages[j + 1]["role"] == "assistant":
                        block_parts.append(
                            f"**Assistant (revised):** {messages[j + 1]['content']}"
                        )
                        seen_indices.add(j + 1)
                    break

            decision_blocks.append("\n\n".join(block_parts))

    if not decision_blocks:
        return None

    text = "\n\n---\n\n".join(decision_blocks)
    if len(text) > MAX_SECTION_CHARS:
        text = text[:MAX_SECTION_CHARS] + "\n\n... (truncated)"
    return text


def extract_corrections(messages: list[dict]) -> str | None:
    """Extract user corrections with preceding assistant context."""
    correction_blocks: list[str] = []

    for i, msg in enumerate(messages):
        if msg["role"] != "user":
            continue

        if any(p.search(msg["content"]) for p in CORRECTION_PATTERNS):
            block_parts: list[str] = []

            # Include preceding assistant message for context
            if i > 0 and messages[i - 1]["role"] == "assistant":
                prev_content = messages[i - 1]["content"]
                if len(prev_content) > 500:
                    prev_content = prev_content[:500] + "..."
                block_parts.append(f"**Assistant (before):** {prev_content}")

            block_parts.append(f"**User (correction):** {msg['content']}")

            # Include assistant response if available
            if i + 1 < len(messages) and messages[i + 1]["role"] == "assistant":
                response = messages[i + 1]["content"]
                if len(response) > 500:
                    response = response[:500] + "..."
                block_parts.append(f"**Assistant (after):** {response}")

            correction_blocks.append("\n\n".join(block_parts))

    if not correction_blocks:
        return None

    text = "\n\n---\n\n".join(correction_blocks)
    if len(text) > MAX_SECTION_CHARS:
        text = text[:MAX_SECTION_CHARS] + "\n\n... (truncated)"
    return text


def slugify(text: str, max_len: int = 60) -> str:
    """Convert text to a filesystem-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:max_len]


def write_inbox_note(
    title: str,
    content: str,
    session_id: str,
    slug: str,
    project: str,
    category: str,
) -> Path:
    """Write a draft inbox note to the vault."""
    VAULT_INBOX.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    frontmatter = "\n".join(
        [
            "---",
            f"created: {date_str}",
            f"source: session-{session_id}",
            f"session_slug: {slug}",
            f"project: {project}",
            "type: session-extract",
            "status: inbox",
            f"tags: [auto-extracted, {category}]",
            "---",
        ]
    )

    note_content = f"{frontmatter}\n\n# {title}\n\n{content}\n"

    file_slug = slugify(f"{category}-{slug}")
    note_path = VAULT_INBOX / f"{file_slug}.md"
    counter = 1
    while note_path.exists():
        note_path = VAULT_INBOX / f"{file_slug}-{counter}.md"
        counter += 1

    note_path.write_text(note_content, encoding="utf-8")
    return note_path


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception as e:
        log(f"ERROR reading stdin: {e}")
        return

    session_id = payload.get("session_id")
    transcript_path = payload.get("transcript_path")

    if not session_id or not transcript_path:
        log(f"Missing session_id or transcript_path. Keys: {sorted(payload.keys())}")
        return

    path = Path(transcript_path)
    if not path.exists():
        log(f"Transcript not found: {transcript_path}")
        return

    try:
        messages, _, slug, project = parse_transcript(path)
    except Exception as e:
        log(f"ERROR parsing transcript: {e}")
        return

    slug = slug or "unknown"

    if len(messages) < MIN_MESSAGES:
        log(f"Session {slug} too short ({len(messages)} messages), skipping")
        return

    notes_created: list[str] = []

    # Extract in priority order
    retro = extract_retrospective(messages)
    if retro:
        note_path = write_inbox_note(
            f"Retrospective from {slug}",
            retro,
            session_id,
            slug,
            project,
            "retrospective",
        )
        notes_created.append(f"retro:{note_path.name}")

    decisions = extract_decisions(messages)
    if decisions:
        note_path = write_inbox_note(
            f"Decisions from {slug}",
            decisions,
            session_id,
            slug,
            project,
            "decisions",
        )
        notes_created.append(f"decisions:{note_path.name}")

    corrections = extract_corrections(messages)
    if corrections:
        note_path = write_inbox_note(
            f"Corrections from {slug}",
            corrections,
            session_id,
            slug,
            project,
            "corrections",
        )
        notes_created.append(f"corrections:{note_path.name}")

    if notes_created:
        log(
            f"Extracted from {slug} ({len(messages)} msgs): "
            + ", ".join(notes_created)
        )
    else:
        log(f"No extractable content in {slug} ({len(messages)} msgs)")


if __name__ == "__main__":
    main()
