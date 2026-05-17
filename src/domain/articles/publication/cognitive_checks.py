"""Cognitive checks — delegate to Part 2's `CognitiveLayer`.

Each check asks the model for a free-form review and parses the
response into `CheckViolation`s. The prompts (in
`src/domain/cognitive_layer/prompts.py`) instruct the model to return
`'CLEAN'` for no issues, or a list of issues prefixed with `- `, one
per line.
"""

from src.domain.articles.entities import Article
from src.domain.cognitive_layer import (
    AssistanceKind,
    CognitiveRequest,
    CognitiveResponse,
)

from .checks import CheckViolation, PublicationCheck, PublicationContext


_CLEAN_TOKEN: str = "CLEAN"
_ISSUE_PREFIX: str = "- "


class CognitiveReviewCheck(PublicationCheck):
    """Base class for checks that delegate to the cognitive layer."""

    code: str
    kind: AssistanceKind

    async def run(
        self, article: Article, ctx: PublicationContext
    ) -> list[CheckViolation]:
        response = await ctx.cognitive.ask(
            CognitiveRequest(kind=self.kind, input=article.body)
        )
        return self._parse(response)

    def _parse(self, response: CognitiveResponse) -> list[CheckViolation]:
        text = response.suggestion.strip()
        if text.upper() == _CLEAN_TOKEN:
            return []

        violations: list[CheckViolation] = []
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith(_ISSUE_PREFIX):
                line = line[len(_ISSUE_PREFIX):].strip()
            if not line:
                continue
            violations.append(
                CheckViolation(code=self.code, field="body", reason=line)
            )
        return violations


class GrammarReviewCheck(CognitiveReviewCheck):
    code = "grammar"
    kind = AssistanceKind.REVIEW_GRAMMAR


class ConsistencyReviewCheck(CognitiveReviewCheck):
    code = "consistency"
    kind = AssistanceKind.REVIEW_CONSISTENCY
