"""Page-aware chunking along readable lines/paragraphs with page provenance.

Chunks are merged visual lines capped by token count; every chunk keeps
its PDF page so citations stay exact. Overlap is 0 by default (embedding
budget is per token).
"""

from __future__ import annotations

import re

import tiktoken

_SENT_SPLIT = re.compile(r"(?<=[.!?؟…:])\s+")
_ENDS_SENT = re.compile(r"[.!?؟…:]['\"”’)]*$")

_enc = None


def count_tokens(text: str) -> int:
    global _enc
    if _enc is None:
        _enc = tiktoken.get_encoding("cl100k_base")
    return len(_enc.encode(text)) if text else 0


def _split_long_line(line: str, max_tokens: int) -> list[str]:
    parts = [p for p in _SENT_SPLIT.split(line) if p.strip()] or [line]
    out, cur = [], ""
    for part in parts:
        trial = f"{cur} {part}".strip()
        if count_tokens(trial) <= max_tokens:
            cur = trial
            continue
        if cur:
            out.append(cur)
        if count_tokens(part) <= max_tokens:
            cur = part
        else:  # single sentence still too long: word-chunk fallback
            words, acc = part.split(), ""
            for word in words:
                trial2 = f"{acc} {word}".strip()
                if count_tokens(trial2) <= max_tokens:
                    acc = trial2
                else:
                    if acc:
                        out.append(acc)
                    acc = word
            cur = acc
    if cur:
        out.append(cur)
    return out


def chunk_text(text: str, max_tokens: int = 600) -> list[dict]:
    """Return [{ordinal, text, tokens}] for one page's text."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    chunks: list[dict] = []
    cur = ""

    def push(piece: str) -> None:
        piece = piece.strip()
        if piece:
            chunks.append({"ordinal": len(chunks), "text": piece, "tokens": count_tokens(piece)})

    for line in lines:
        trial = f"{cur} {line}".strip() if cur else line
        if count_tokens(trial) <= max_tokens:
            # Prefer starting a fresh chunk after sentence end past half fill.
            if cur and _ENDS_SENT.search(cur) and count_tokens(cur) >= max_tokens // 2:
                push(cur)
                cur = line
            else:
                cur = trial
        else:
            if cur:
                push(cur)
            if count_tokens(line) <= max_tokens:
                cur = line
            else:
                for piece in _split_long_line(line, max_tokens):
                    push(piece)
                cur = ""
    if cur:
        push(cur)
    return chunks
