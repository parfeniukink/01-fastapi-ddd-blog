"""Five mechanical (non-cognitive) publication checks.

Cheap to run. These compose ``submission_pipeline()`` — the gate for
``/articles/{slug}/submit``. Any violation blocks the transition out
of DRAFT, so the author cannot push to review until every mechanical
rule passes.
"""

import re

from src.domain.articles.authors import is_authorized_to_publish
from src.domain.articles.entities import Article
from src.domain.articles.policies import find_stop_word

from .checks import CheckViolation, PublicationCheck, PublicationContext


class AuthorityCheck(PublicationCheck):
    code = "authority"

    async def run(
        self, article: Article, ctx: PublicationContext
    ) -> list[CheckViolation]:
        if is_authorized_to_publish(article.author):
            return []
        return [
            CheckViolation(
                code=self.code,
                field="author",
                reason=f"author {article.author!r} is not allowed to publish",
            )
        ]


class StopWordsCheck(PublicationCheck):
    code = "stop_word"

    async def run(
        self, article: Article, ctx: PublicationContext
    ) -> list[CheckViolation]:
        violations: list[CheckViolation] = []
        for field in ("title", "summary", "body"):
            text: str = getattr(article, field)
            word = find_stop_word(text)
            if word is not None:
                violations.append(
                    CheckViolation(
                        code=self.code,
                        field=field,
                        reason=f"contains forbidden word {word!r}",
                    )
                )
        return violations


class StructureCheck(PublicationCheck):
    code = "structure"

    title_min: int = 10
    title_max: int = 200
    summary_min: int = 50
    summary_max: int = 500
    body_min: int = 500

    async def run(
        self, article: Article, ctx: PublicationContext
    ) -> list[CheckViolation]:
        violations: list[CheckViolation] = []
        if not self.title_min <= len(article.title) <= self.title_max:
            violations.append(
                self._range_violation("title", self.title_min, self.title_max)
            )
        if not self.summary_min <= len(article.summary) <= self.summary_max:
            violations.append(
                self._range_violation("summary", self.summary_min, self.summary_max)
            )
        if len(article.body) < self.body_min:
            violations.append(
                CheckViolation(
                    code=self.code,
                    field="body",
                    reason=f"body must be at least {self.body_min} characters",
                )
            )
        return violations

    def _range_violation(self, field: str, lo: int, hi: int) -> CheckViolation:
        return CheckViolation(
            code=self.code,
            field=field,
            reason=f"length must be between {lo} and {hi} characters",
        )


class CitationCheck(PublicationCheck):
    code = "citation"

    URL_PATTERN: re.Pattern = re.compile(r"https?://\S+")

    async def run(
        self, article: Article, ctx: PublicationContext
    ) -> list[CheckViolation]:
        if self.URL_PATTERN.search(article.body):
            return []
        return [
            CheckViolation(
                code=self.code,
                field="body",
                reason="article body must contain at least one external citation link",
            )
        ]


class DuplicateTitleCheck(PublicationCheck):
    code = "duplicate_title"

    async def run(
        self, article: Article, ctx: PublicationContext
    ) -> list[CheckViolation]:
        existing = await ctx.repository.load_articles()
        for summary in existing:
            if summary.id != article.id and summary.title == article.title:
                return [
                    CheckViolation(
                        code=self.code,
                        field="title",
                        reason=f"title is also used by article {summary.slug!r}",
                    )
                ]
        return []
