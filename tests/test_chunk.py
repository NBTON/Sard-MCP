"""Unit tests: page-aware chunking."""

from sard_mcp.chunk import chunk_text, count_tokens


def test_empty_text_no_chunks():
    assert chunk_text("") == []
    assert chunk_text("   \n  ") == []


def test_short_page_single_chunk():
    chunks = chunk_text("سطر أول\nسطر ثان")
    assert len(chunks) == 1
    assert chunks[0]["ordinal"] == 0
    assert "سطر أول" in chunks[0]["text"] and "سطر ثان" in chunks[0]["text"]


def test_chunks_respect_token_cap():
    para = "كلمة " * 400  # ~400 tokens
    chunks = chunk_text(f"{para}\n{para}\n{para}", max_tokens=600)
    assert len(chunks) >= 2
    for c in chunks:
        assert c["tokens"] <= 600, c["tokens"]
    assert [c["ordinal"] for c in chunks] == list(range(len(chunks)))


def test_long_sentence_word_fallback():
    line = " ".join(f"w{i}" for i in range(2000))
    chunks = chunk_text(line, max_tokens=600)
    assert len(chunks) > 1
    for c in chunks:
        assert c["tokens"] <= 600


def test_count_tokens_arabic_english():
    assert count_tokens("") == 0
    assert count_tokens("hello") == 1
    assert count_tokens("الضيافة العربية") > 1
