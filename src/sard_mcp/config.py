"""Configuration: paths, model, budgets. Secrets stay in local `.env` only."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def default_home() -> Path:
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~/.local/share")
    return Path(base) / "SardMCP"


@dataclass(frozen=True)
class Settings:
    home: Path
    db_path: Path
    source_dir: Path
    embedding_model: str = "openai/text-embedding-3-small"
    embedding_dims: int = 1536
    embedding_max_tokens: int = 8191
    openrouter_base: str = "https://openrouter.ai/api/v1"
    price_per_mtok_usd: float = 0.02
    # Key limit is $4.00 (checked live); preserve $1.00 -> app cap $3.00.
    first_index_budget_usd: float = 1.00
    cumulative_budget_usd: float = 3.00
    corpus_revision: str = "r1"

    @property
    def api_key(self) -> str | None:
        v = os.environ.get("OPENROUTER_API_KEY", "").strip().strip('"').strip("'")
        return v or None


def load_settings(env_file: Path | None = None) -> Settings:
    """Load `.env` (KEY=VALUE lines, no shell expansion) then build settings."""
    override = os.environ.get("SARD_ENV_FILE", "")
    path = env_file or (Path(override) if override else (PROJECT_ROOT / ".env"))
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
    home = Path(os.environ.get("SARD_HOME", str(default_home())))
    return Settings(
        home=home,
        db_path=Path(os.environ.get("SARD_DB", str(home / "sard.db"))),
        source_dir=Path(os.environ.get("SARD_SOURCE_DIR", r"C:\Users\nawaf\OneDrive - KFUPM\Culture")),
        embedding_model=os.environ.get("SARD_EMBED_MODEL", "openai/text-embedding-3-small"),
        corpus_revision=os.environ.get("SARD_CORPUS_REV", "r1"),
    )
