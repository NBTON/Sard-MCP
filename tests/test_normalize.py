"""Unit tests: search-text normalization and script ratio."""

from sard_mcp.normalize import arabic_ratio, normalize_search, strip_stopwords


def test_alef_variants_unified():
    assert normalize_search("الأبعاد الاجتماعية") == normalize_search("األبعاد االجتماعية")


def test_pdfium_defect_transparent():
    # PDFium emits األ for الأ; both normalize identically for search.
    assert normalize_search("الأرز") == normalize_search("األرز")


def test_diacritics_and_tatweel_stripped():
    assert normalize_search("سُجلت التواصل") == "سجلت التواصل"


def test_digits_unified_and_lowercased():
    assert normalize_search("عام ٢٠١٥م Urban") == "عام 2015م urban"


def test_replacement_char_removed():
    assert "�" not in normalize_search("حا�ل")


def test_arabic_ratio_orders():
    assert arabic_ratio("المجلس العربي") == 1.0
    assert arabic_ratio("Urban Heritage Sector") == 0.0
    assert 0.0 < arabic_ratio("القهوة Coffee") < 1.0
    assert arabic_ratio("") == 0.0


def test_stopwords_stripped_english():
    q = normalize_search("According to the available source, what is hanini made from?")
    stripped = strip_stopwords(q)
    assert "hanini" in stripped.split()
    for junk in ("according", "available", "source", "what", "from"):
        assert junk not in stripped.split()


def test_stopwords_stripped_arabic():
    q = normalize_search("ما المكونات التي يذكرها المرجع للكليجا؟")
    stripped = strip_stopwords(q)
    assert "للكليجا" in stripped
    assert normalize_search("المرجع") not in stripped.split()


def test_english_source_hint():
    from sard_mcp.normalize import english_source_hint

    assert english_source_hint("ما الذي يذكره المرجع الإنجليزي؟")
    assert english_source_hint("what does the English reference say?")
    assert not english_source_hint("How does the source connect coffee with hospitality?")
    assert not english_source_hint("ما المكونات؟")


def test_expand_query_aliases():
    from sard_mcp.normalize import normalize_search
    from sard_mcp.search import expand_query

    extra, applied = expand_query(normalize_search("What is hanini made from?"))
    assert normalize_search("الحنيني") in extra
    assert applied
    extra, applied = expand_query(normalize_search("qasr al-hukm history"))
    assert normalize_search("قصر الحكم") in extra
