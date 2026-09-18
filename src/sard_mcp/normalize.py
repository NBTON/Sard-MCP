"""Arabic-aware normalization for *search text only*.

Raw extraction and reviewed transcriptions are preserved verbatim; this
module only derives the normalized form used for FTS keyword matching.
It also absorbs systematic PDFium defects (e.g. `األبعاد` for `الأبعاد`):
both spellings normalize to the same form.
"""

from __future__ import annotations

import re
import unicodedata

_ALEF = {"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا"}
_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
_WS = re.compile(r"\s+")
_DIACRITICS = re.compile("[\u064b-\u0652\u0670\u0640]")

STOP_EN = frozenset("""
a an the and or but if then else when what which who whom whose what where why how
is are was were be been being do does did have has had having i you he she it we they them
this that these those in on at to for of with by from as into through during about into over
after before between out up down off again further once here there all any both each few more
most other some such no nor not only own same so than too very can will just should now
according available source sources passage mention mentioned say says said give provide
made make makes many much like likely use used using often name named part tell tells
describe describes describe explain explains include includes including contain contains
within without also well may might must shall per one two three first second list
""".split())

STOP_AR = frozenset("""
من في على إلى عن مع هذا هذه ذلك التي الذي الذين ما ماذا كيف هل قد لا نعم
هو هي هم نحن أن إن أو و ثم إذا كان كانت يكون تكون بين بعد قبل عند غير
كل بعض كما هل وما وهل المرجع المصدر المصادر المتاحة يذكر تذكر اذكر أعطني
يقول تقول التالي التالية
""".split())
STOP_AR_NORM = frozenset()  # computed below after normalize_search is defined


def strip_stopwords(normalized_query: str) -> str:
    keep = [t for t in normalized_query.split() if t not in STOP_EN and t not in STOP_AR_NORM]
    return " ".join(keep)


# Explicit source-language scoping ("the English reference"). English-only by
# design: an Arabic hint is unsafe because "Arabic coffee" is a dish name.
_EN_HINT = re.compile(r"الانجليز|الإنجليز|english")


def english_source_hint(raw_query: str) -> bool:
    return bool(_EN_HINT.search(raw_query.lower()))


def normalize_search(text: str) -> str:
    # Repair systematic PDFium transposition (validated on anchor renders):
    # الX written as اXل for X in {أ، إ، آ، ا} (e.g. األبعاد for الأبعاد).
    # Applied symmetrically to indexed text and queries; correct text has no
    # in-word اXل trigrams so it passes through unchanged.
    t = re.sub("ا([أإآ])ل", r"ال\1", text)
    t = re.sub("اال(?=[\u0600-\u06ff])", "الا", t)
    t = t.translate(_DIGITS)
    t = _DIACRITICS.sub("", t)
    for src, dst in _ALEF.items():
        t = t.replace(src, dst)
    t = t.replace("ؤ", "و").replace("ئ", "ي").replace("ة", "ه").replace("ى", "ي")
    t = "".join(ch for ch in t if ch != "�" and unicodedata.category(ch)[0] != "C")
    t = t.lower()
    return _WS.sub(" ", t).strip()


STOP_AR_NORM = frozenset(normalize_search(w) for w in STOP_AR)


def arabic_ratio(text: str) -> float:
    """Fraction of letters in the Arabic Unicode blocks (order-independent)."""
    arabic = latin = 0
    for ch in text:
        if "\u0600" <= ch <= "\u06ff" or "\ufb50" <= ch <= "\ufdff" or "\ufe70" <= ch <= "\ufefc":
            arabic += 1
        elif ch.isalpha():
            latin += 1
    total = arabic + latin
    return (arabic / total) if total else 0.0
