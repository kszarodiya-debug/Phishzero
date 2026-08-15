"""Deterministic preprocessing for subject-plus-body text classification."""

from __future__ import annotations

from html import unescape
import re


_SCRIPT_STYLE_PATTERN = re.compile(r"<\s*(script|style)\b[^>]*>.*?<\s*/\s*\1\s*>", re.IGNORECASE | re.DOTALL)
_HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
_URL_PATTERN = re.compile(r"https?://\S+", re.IGNORECASE)
_NON_WORD_PATTERN = re.compile(r"[^a-z0-9]+")


def normalize_text(text: str | None) -> str:
    """Normalize text without executing HTML or JavaScript content."""
    if not text:
        return ""
    normalized = unescape(str(text))
    normalized = _SCRIPT_STYLE_PATTERN.sub(" ", normalized)
    normalized = _HTML_TAG_PATTERN.sub(" ", normalized)
    normalized = _URL_PATTERN.sub(" url ", normalized)
    normalized = normalized.casefold()
    normalized = _NON_WORD_PATTERN.sub(" ", normalized)
    return " ".join(normalized.split())


def combine_subject_body(subject: str | None, body: str | None) -> str:
    """Combine the two model inputs while retaining subject/body context."""
    return normalize_text(f"subject {subject or ''} body {body or ''}")

