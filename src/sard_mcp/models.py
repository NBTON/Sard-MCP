"""Pydantic contracts for the three read-only tools."""

from __future__ import annotations

from pydantic import BaseModel, Field

COLLECTION_URL = "https://culturalhub.moc.gov.sa/ar-SA/HeritageBookListing"
COLLECTION_PROVENANCE = "user_provided_collection"


class SearchInput(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    region: str | None = Field(default=None, max_length=80)
    topic: str | None = Field(default=None, max_length=80)
    lang: str | None = Field(default=None, description="Source language filter: 'ar' or 'en'.")
    doc_ids: list[str] | None = Field(default=None, max_length=10)
    top_k: int = Field(default=5, ge=1, le=10)


class PassageInput(BaseModel):
    pid: str = Field(min_length=1, max_length=200)
    context_chars: int = Field(default=600, ge=0, le=2000)


class CoverageInput(BaseModel):
    region: str | None = Field(default=None, max_length=80)
    topic: str | None = Field(default=None, max_length=80)
