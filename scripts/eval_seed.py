"""Run seed (or held-out) retrieval cases against the live index.

Development fixture runner: reports supporting-passage hit@5 on supported
cases and shows retrieved evidence for trap cases (manual judgment).
Saves a full JSON trace; prints a compact table.

Usage:  uv run python scripts/eval_seed.py [--seed evals/seed_cases.json]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sard_mcp import search as S  # noqa: E402
from sard_mcp import store  # noqa: E402
from sard_mcp.config import PROJECT_ROOT, load_settings  # noqa: E402
from sard_mcp.models import SearchInput  # noqa: E402

SCORED = {"supported", "supported_cross_language", "supported_regional"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", default=str(PROJECT_ROOT / "evals" / "seed_cases.json"))
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()
    seed = json.loads(Path(args.seed).read_text(encoding="utf-8"))
    settings = load_settings()
    conn = store.open_db(settings.db_path)
    results = []
    hits = scored = 0
    for case in seed["cases"]:
        t0 = time.perf_counter()
        try:
            out = S.search(SearchInput(query=case["query"], top_k=args.top_k), settings, conn)
            err = None
        except Exception as exc:  # noqa: BLE001 - eval must not abort
            out, err = {"results": [], "retrieval_mode": "error", "warnings": []}, repr(exc)
        dt = time.perf_counter() - t0
        got = {(h["doc_id"], h["pdf_page"]) for h in out["results"]}
        want = {(e["document"], e["pdf_page"]) for e in case.get("evidence", [])}
        scored_case = case["type"] in SCORED
        hit = bool(got & want) if scored_case else None
        if scored_case:
            scored += 1
            hits += bool(hit)
        results.append({
            "id": case["id"], "type": case["type"], "hit": hit, "mode": out["retrieval_mode"],
            "ms": round(dt * 1000), "pids": [h["pid"] for h in out["results"]],
            "warnings": out["warnings"], "error": err,
        })
        mark = "HIT " if hit else ("miss" if scored_case else "trap")
        print(f"{mark} {case['id']} [{case['type']}] mode={out['retrieval_mode']} "
              f"{results[-1]['ms']}ms pids={results[-1]['pids']}", flush=True)
    print(f"supported hit@{args.top_k}: {hits}/{scored}")
    dest = settings.home / f"eval_{Path(args.seed).stem}_{time.strftime('%Y%m%d-%H%M%S')}.json"
    dest.write_text(json.dumps({"seed": args.seed, "results": results,
                                "summary": {"hits": hits, "scored": scored}}, ensure_ascii=False, indent=1),
                    encoding="utf-8")
    print(f"trace: {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
