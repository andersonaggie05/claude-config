#!/usr/bin/env python3
"""brain-ingest: Fetch raw content from video/audio/documents and drop into vault inbox.

Two-stage workflow:
  Stage 1 (this script): Fetch raw content, create inbox note with metadata
  Stage 2 (Claude /vault-ingest): Extract claims/frameworks, create proper vault notes

Usage:
  python brain-ingest.py "https://youtube.com/watch?v=..."   # YouTube transcript
  python brain-ingest.py ~/Downloads/paper.pdf                # PDF text extraction
  python brain-ingest.py ~/Downloads/transcript.txt           # Raw text file
  python brain-ingest.py --stdin                              # Read from stdin
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

VAULT_INBOX = Path.home() / "vault" / "inbox"


def slugify(text: str, max_len: int = 80) -> str:
    """Convert text to a filesystem-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:max_len]


def extract_youtube_id(url: str) -> str | None:
    """Extract video ID from various YouTube URL formats."""
    parsed = urlparse(url)
    if parsed.hostname in ("www.youtube.com", "youtube.com", "m.youtube.com"):
        return parse_qs(parsed.query).get("v", [None])[0]
    if parsed.hostname in ("youtu.be",):
        return parsed.path.lstrip("/")
    return None


def ingest_youtube(url: str) -> tuple[str, str, dict]:
    """Fetch YouTube transcript and metadata. Returns (title, content, metadata)."""
    from youtube_transcript_api import YouTubeTranscriptApi

    video_id = extract_youtube_id(url)
    if not video_id:
        raise ValueError(f"Could not extract video ID from: {url}")

    # Fetch transcript
    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

    # Prefer manually created, fall back to auto-generated
    transcript = None
    for t in transcript_list:
        if not t.is_generated:
            transcript = t
            break
    if transcript is None:
        transcript = transcript_list.find_generated_transcript(["en"])

    entries = transcript.fetch()

    # Build readable transcript
    lines = []
    for entry in entries:
        text = entry.get("text", entry.text if hasattr(entry, "text") else str(entry))
        lines.append(text)
    content = " ".join(lines)

    # Try to get a title (basic approach)
    title = f"youtube-{video_id}"

    metadata = {
        "source": url,
        "type": "youtube-transcript",
        "video_id": video_id,
    }

    return title, content, metadata


def ingest_pdf(file_path: Path) -> tuple[str, str, dict]:
    """Extract text from a PDF file. Returns (title, content, metadata)."""
    from PyPDF2 import PdfReader

    if not file_path.exists():
        raise FileNotFoundError(f"PDF not found: {file_path}")

    reader = PdfReader(str(file_path))

    if reader.is_encrypted:
        raise ValueError(f"PDF is encrypted: {file_path}")

    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            pages.append(f"--- Page {i + 1} ---\n{text}")

    if not pages:
        raise ValueError(f"No text could be extracted from: {file_path}")

    content = "\n\n".join(pages)
    title = file_path.stem

    metadata = {
        "source": str(file_path),
        "type": "pdf",
        "pages": len(reader.pages),
    }

    return title, content, metadata


def ingest_text(file_path: Path) -> tuple[str, str, dict]:
    """Read a text file. Returns (title, content, metadata)."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    content = file_path.read_text(encoding="utf-8", errors="replace")
    title = file_path.stem

    metadata = {
        "source": str(file_path),
        "type": "text",
    }

    return title, content, metadata


def ingest_stdin() -> tuple[str, str, dict]:
    """Read content from stdin. Returns (title, content, metadata)."""
    content = sys.stdin.read()
    if not content.strip():
        raise ValueError("No content received from stdin")

    title = f"stdin-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"

    metadata = {
        "source": "stdin",
        "type": "text",
    }

    return title, content, metadata


def write_inbox_note(title: str, content: str, metadata: dict) -> Path:
    """Write an inbox note to the vault."""
    VAULT_INBOX.mkdir(parents=True, exist_ok=True)

    slug = slugify(title)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Build frontmatter
    frontmatter_lines = [
        "---",
        f"created: {date_str}",
        f"source: {metadata['source']}",
        f"type: {metadata['type']}",
        "status: inbox",
        "tags: [ingested]",
    ]

    # Add extra metadata
    for key, value in metadata.items():
        if key not in ("source", "type"):
            frontmatter_lines.append(f"{key}: {value}")

    frontmatter_lines.append("---")
    frontmatter = "\n".join(frontmatter_lines)

    # Truncate very long content (>100k chars) with a note
    if len(content) > 100_000:
        content = content[:100_000] + "\n\n... (truncated at 100,000 characters)"

    note_content = f"{frontmatter}\n\n# {title}\n\n{content}\n"

    # Avoid filename collisions
    note_path = VAULT_INBOX / f"{slug}.md"
    counter = 1
    while note_path.exists():
        note_path = VAULT_INBOX / f"{slug}-{counter}.md"
        counter += 1

    note_path.write_text(note_content, encoding="utf-8")
    return note_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest content into Obsidian vault inbox"
    )
    parser.add_argument(
        "source",
        nargs="?",
        help="YouTube URL, PDF path, or text file path",
    )
    parser.add_argument(
        "--stdin",
        action="store_true",
        help="Read content from stdin",
    )
    args = parser.parse_args()

    if not args.source and not args.stdin:
        parser.print_help()
        sys.exit(1)

    try:
        if args.stdin:
            title, content, metadata = ingest_stdin()
        elif args.source.startswith(("http://", "https://")):
            # URL — check if YouTube
            if extract_youtube_id(args.source):
                title, content, metadata = ingest_youtube(args.source)
            else:
                print(f"Error: Only YouTube URLs are supported. Got: {args.source}")
                sys.exit(1)
        else:
            # Local file
            file_path = Path(args.source).expanduser().resolve()
            if file_path.suffix.lower() == ".pdf":
                title, content, metadata = ingest_pdf(file_path)
            else:
                title, content, metadata = ingest_text(file_path)

        note_path = write_inbox_note(title, content, metadata)
        print(f"Note created at {note_path}")
        print("Use /vault-ingest to process it into structured vault notes.")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
