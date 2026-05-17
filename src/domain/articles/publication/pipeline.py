"""Publication pipelines — composes checks and collects violations.

Two pipelines, one class:

- ``submission_pipeline()`` runs the **mechanical** checks (author
  authority, stop words, structure, citation, duplicate title). It
  is the gate for ``/articles/{slug}/submit`` and BLOCKS on any
  violation — the author cannot push to review until the article is
  clean against the editorial team's mechanical rules.

- ``editorial_pipeline()`` runs the **cognitive** checks (grammar,
  consistency). It is the advisory step invoked when a supervisor
  picks up an article via ``/articles/{slug}/review`` — the LLM
  findings are returned alongside the article so the supervisor
  can read them before deciding to approve or reject. The pipeline
  itself never blocks the transition; the supervisor does.

Splitting the pipeline matches role ownership. The user owns the
submission gate (they can fix every violation). The supervisor owns
the review and uses the cognitive findings as input to a human
decision.
"""

from collections.abc import Sequence

from src.domain.articles.entities import Article
from src.domain.base import DomainModel

from .checks import CheckViolation, PublicationCheck, PublicationContext
from .cognitive_checks import ConsistencyReviewCheck, GrammarReviewCheck
from .mechanical_checks import (
    AuthorityCheck,
    CitationCheck,
    DuplicateTitleCheck,
    StopWordsCheck,
    StructureCheck,
)


class PipelineResult(DomainModel):
    passed: bool
    violations: list[CheckViolation]


class PublicationPipeline:
    def __init__(self, checks: Sequence[PublicationCheck]) -> None:
        self._checks = tuple(checks)

    async def run(
        self,
        article: Article,
        ctx: PublicationContext,
    ) -> PipelineResult:
        """Run every check and collect their violations."""

        violations: list[CheckViolation] = []
        for check in self._checks:
            violations.extend(await check.run(article, ctx))
        return PipelineResult(passed=not violations, violations=violations)


def submission_pipeline() -> PublicationPipeline:
    """5 mechanical checks — gate for `/submit`."""

    return PublicationPipeline(
        checks=(
            AuthorityCheck(),
            StopWordsCheck(),
            StructureCheck(),
            CitationCheck(),
            DuplicateTitleCheck(),
        ),
    )


def editorial_pipeline() -> PublicationPipeline:
    """2 cognitive checks — advisory input for `/review`."""

    return PublicationPipeline(
        checks=(
            GrammarReviewCheck(),
            ConsistencyReviewCheck(),
        ),
    )
