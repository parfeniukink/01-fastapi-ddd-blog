"""Public shapes for /articles/imports."""

from pydantic import Field

from src.domain.articles import ExternalSource
from src.http._base import PublicModel


class ImportRequest(PublicModel):
    account: str = Field(min_length=1)


class ImportReportPublic(PublicModel):
    source: ExternalSource
    account: str
    imported: int
    skipped: int
    failed: int
