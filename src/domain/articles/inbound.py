"""Inbound integration shapes and contract — part of the articles aggregate.

An inbound import is "an article coming in from somewhere else", so
the contract sits with the rest of the article aggregate. Concrete
adapters (Medium, Reddit) live in `infrastructure/integrations/` and
implement the abstract source defined here.
"""

import abc
from collections.abc import AsyncIterator
from enum import StrEnum

from src.domain.base import DomainModel

from .entities import ArticleDraft


class ExternalSource(StrEnum):
    MEDIUM = "medium"
    REDDIT = "reddit"


class ImportReport(DomainModel):
    source: ExternalSource
    account: str
    imported: int = 0
    skipped: int = 0
    failed: int = 0


class ExternalArticleSource(abc.ABC):
    # Subclasses set `kind` so the use case can stamp the report with
    # the source name without asking which subclass it received.
    kind: ExternalSource

    @abc.abstractmethod
    def fetch(self, account: str) -> AsyncIterator[ArticleDraft]:
        """Yield ArticleDrafts found under `account` on this source."""
