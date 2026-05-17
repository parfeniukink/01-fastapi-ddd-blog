"""PublicationCheck ABC, the CheckViolation value object, and the
shared PublicationContext that every check needs.

PublicationContext lives here (next to the ABC) rather than in
``pipeline.py`` so the checks do not have to reach across modules to
spell their own dependency shape.
"""

import abc
from dataclasses import dataclass

from src.domain.articles.entities import Article
from src.domain.articles.repository import BookshelfRepository
from src.domain.base import DomainModel
from src.domain.cognitive_layer import CognitiveLayer


class CheckViolation(DomainModel):
    code: str            # machine-readable: "authority", "stop_word", ...
    field: str | None    # which article field, when applicable
    reason: str          # human-readable explanation


@dataclass(frozen=True)
class PublicationContext:
    """Carries the shared dependencies the checks need."""

    repository: BookshelfRepository
    cognitive: CognitiveLayer


class PublicationCheck(abc.ABC):
    """One step of a publication pipeline.

    Each check returns a list of violations — empty means it passed.
    The pipeline collects violations from every check before deciding.
    """

    code: str

    @abc.abstractmethod
    async def run(
        self,
        article: Article,
        ctx: PublicationContext,
    ) -> list[CheckViolation]: ...
