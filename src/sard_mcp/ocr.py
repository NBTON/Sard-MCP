"""Local OCR fallback for scanned-image PDFs (read-only on sources).

The 15 regional books added in corpus rev r2 have no text layer at all, so
the pdfium/pypdf engines return zero chars on every page. This module OCRs
rendered pages with a local Tesseract (Arabic + English, tessdata_best) and
caches the result per (file checksum, page) under SARD_HOME/ocr, so dry-run
and import never OCR the same page twice. No paid calls are made here.

Quality gate inputs per page: recognized text, mean word confidence from
the TSV output, and word count. Measured separation (quality-sample/r2):
clean prose 68-91, decorative titles 69-78, photo/artwork garbage ~35,
blank 0 words. The CLI approves at mean confidence >= 60.
"""

from __future__ import annotations

import csv
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ENGINE_LABEL = "ocr-tesseract-ara-eng"
OCR_LANGS = "ara+eng"
MIN_CONF = 60.0
MIN_WORDS = 5
OCR_TIMEOUT_S = 240
MAX_RENDER_DIM = 3600

_TESSERACT_BIN: str | None = None
# pypdfium2 document loads are not thread-safe (concurrent opens fail with
# "Data format error"), so all renders are serialized. Tesseract itself runs
# in separate processes and stays parallel.
_RENDER_LOCK = threading.Lock()

_LONG_LATIN = re.compile(r"[A-Za-z]{4,}")
_SHORT_LATIN_TOKEN = re.compile(r"^[^A-Za-z0-9]*[A-Za-z]{1,3}[^A-Za-z0-9]*$")


def clean_ocr_text(text: str) -> str:
    """Drop 1-3 letter Latin fragments (eng-model misreads of Arabic marks).

    With ara+eng, stray marks and diacritics are often read as 'a', 'ee',
    'oe' (~100k such tokens corpus-wide, often clustered: 'pee ge'). A
    short Latin token is dropped unless a neighbouring token carries a
    Latin run of 4+ letters, so bibliographies and foreign terms
    ('G. Mursi', 'Alois Musil', 'Ayn Zubaydah') survive.
    """
    parts = re.split(r"(\s+)", text)
    n = len(parts)

    def anchored(i: int) -> bool:
        return 0 <= i < n and bool(_LONG_LATIN.search(parts[i]))

    out = []
    for i, part in enumerate(parts):
        if (part.strip() and _SHORT_LATIN_TOKEN.match(part)
                and not anchored(i - 2) and not anchored(i + 2)):
            continue
        out.append(part)
    return "".join(out)


def tesseract_bin() -> str:
    """Locate the tesseract binary (PATH, then the well-known install dir)."""
    global _TESSERACT_BIN
    if _TESSERACT_BIN is None:
        found = shutil.which("tesseract")
        if not found:
            fallback = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
            if fallback.exists():
                found = str(fallback)
        if not found:
            raise RuntimeError("tesseract binary not found (install Tesseract OCR 5.x).")
        _TESSERACT_BIN = found
    return _TESSERACT_BIN


def tesseract_env() -> dict:
    """Environment for tesseract: user-local tessdata wins when present."""
    env = dict(os.environ)
    if "TESSDATA_PREFIX" not in env:
        local = Path(os.environ.get("LOCALAPPDATA", "")) / "SardMCP" / "tessdata"
        if (local / "ara.traineddata").exists():
            env["TESSDATA_PREFIX"] = str(local)
    # Single-threaded engines: parallelism comes from worker processes, which
    # scales linearly; letting every engine multithread oversubscribes CPUs.
    env.setdefault("OMP_THREAD_LIMIT", "1")
    return env


def tesseract_version() -> str:
    try:
        out = subprocess.run(
            [tesseract_bin(), "--version"], capture_output=True, text=True,
            timeout=30, env=tesseract_env()).stdout
        return out.splitlines()[0].strip() if out else "unknown"
    except Exception:
        return "unknown"


def check_arabic() -> None:
    langs = subprocess.run(
        [tesseract_bin(), "--list-langs"], capture_output=True, text=True,
        timeout=60, env=tesseract_env())
    have = langs.stdout + langs.stderr
    for lang in OCR_LANGS.split("+"):
        if lang not in have:
            raise RuntimeError(f"Tesseract data ({lang}.traineddata) not found.")


def cache_paths(cache_dir: Path, pdf: Path, checksum: str, page1: int) -> tuple[Path, Path]:
    base = f"{pdf.stem}_{checksum[:12]}__p{page1:03d}"
    return cache_dir / (base + ".txt"), cache_dir / (base + ".json")


def read_cache(cache_dir: Path, pdf: Path, checksum: str, page1: int) -> dict | None:
    txt_path, meta_path = cache_paths(cache_dir, pdf, checksum, page1)
    if txt_path.exists() and meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            if meta.get("langs", "ara") != OCR_LANGS or not meta.get("clean"):
                return None  # stale method: re-OCR rather than mix variants
            meta["text"] = txt_path.read_text(encoding="utf-8")
            meta["cached"] = True
            return meta
        except (OSError, ValueError):
            return None
    return None


def _render_for_ocr(pdf: Path, idx0: int, dest: Path) -> None:
    """Render at ~300 DPI equivalent, capped so tesseract cannot hang."""
    import pypdfium2

    with _RENDER_LOCK:
        doc = pypdfium2.PdfDocument(str(pdf))
        try:
            w, h = doc[idx0].get_size()
            scale = min(300.0 / 72.0, MAX_RENDER_DIM / max(w, h))
            doc[idx0].render(scale=scale).to_pil().convert("L").save(str(dest))
        finally:
            doc.close()


def ocr_page_uncached(pdf: Path, idx0: int, workdir: Path) -> dict:
    """OCR one page (0-based). Returns text/mean_conf/words/ms or error."""
    import time

    t0 = time.time()
    env = tesseract_env()
    with tempfile.TemporaryDirectory(dir=str(workdir)) as tmp:
        img = Path(tmp) / "page.png"
        try:
            _render_for_ocr(pdf, idx0, img)
        except Exception as exc:  # noqa: BLE001 - recorded, page excluded
            return {"error": f"render_failed: {type(exc).__name__}: {exc}"}
        base = str(Path(tmp) / "out")
        try:
            proc = subprocess.run(
                [tesseract_bin(), str(img), base, "-l", OCR_LANGS,
                 "--psm", "6", "txt", "tsv"],
                capture_output=True, text=True, timeout=OCR_TIMEOUT_S, env=env)
        except subprocess.TimeoutExpired:
            return {"error": "ocr_timeout"}
        if proc.returncode != 0:
            return {"error": f"ocr_failed rc={proc.returncode}: {proc.stderr[:200]}"}
        try:
            text = clean_ocr_text(Path(base + ".txt").read_text(encoding="utf-8"))
        except OSError:
            text = ""
        confs: list[float] = []
        try:
            with open(base + ".tsv", encoding="utf-8", newline="") as fh:
                for row in csv.DictReader(fh, delimiter="\t"):
                    if row.get("level") == "5" and (row.get("text") or "").strip():
                        try:
                            confs.append(float(row["conf"]))
                        except ValueError:
                            pass
        except OSError:
            pass
    ms = int((time.time() - t0) * 1000)
    return {
        "text": text,
        "mean_conf": round(sum(confs) / len(confs), 1) if confs else 0.0,
        "words": len(confs),
        "ms": ms,
        "langs": OCR_LANGS,
        "clean": 1,
        "method": f"{tesseract_version()} {OCR_LANGS} psm6 + fragfilter",
    }


def ocr_page(pdf: Path, idx0: int, checksum: str, cache_dir: Path,
             refresh: bool = False) -> dict:
    """OCR one page with cache. idx0 is 0-based; cache key is 1-based."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    if not refresh:
        hit = read_cache(cache_dir, pdf, checksum, idx0 + 1)
        if hit is not None:
            return hit
    res = ocr_page_uncached(pdf, idx0, cache_dir)
    txt_path, meta_path = cache_paths(cache_dir, pdf, checksum, idx0 + 1)
    if "error" not in res:
        txt_path.write_text(res["text"], encoding="utf-8")
        sidecar = {k: v for k, v in res.items() if k != "text"}
        sidecar["checksum"] = checksum
        meta_path.write_text(json.dumps(sidecar, ensure_ascii=False), encoding="utf-8")
        res["cached"] = False
    return res


def ocr_doc_pages(pdf: Path, pages: list[int], checksum: str, cache_dir: Path,
                  workers: int = 4, refresh: bool = False,
                  progress: bool = True) -> dict[int, dict]:
    """OCR selected 1-based pages in parallel. Returns {page: result}."""
    check_arabic()
    out: dict[int, dict] = {}
    missing = [p for p in pages
               if refresh or read_cache(cache_dir, pdf, checksum, p) is None]
    if progress:
        print(f"  ocr {pdf.name}: {len(pages) - len(missing)}/{len(pages)} cached",
              flush=True)
    if missing:
        with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
            results = pool.map(
                lambda p: ocr_page(pdf, p - 1, checksum, cache_dir, refresh),
                missing)
            for p, res in zip(missing, results):
                out[p] = res
                if progress and (len(out) % 25 == 0 or len(out) == len(missing)):
                    print(f"  ocr {pdf.name}: {len(out)}/{len(missing)} done",
                          flush=True)
        errs = Counter(r.get("error", "").split(":")[0] for r in out.values() if "error" in r)
        if errs and progress:
            print(f"  ocr {pdf.name}: ERRORS {dict(errs)}", flush=True)
    for p in pages:
        if p not in out:
            hit = read_cache(cache_dir, pdf, checksum, p)
            assert hit is not None
            out[p] = hit
    return out
