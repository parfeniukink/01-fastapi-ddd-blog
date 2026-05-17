"""Article use cases — CRUD, editorial actions, inbound imports, publication.

Publication use cases hardcode the acting role (``UserRole.USER`` or
``UserRole.SUPERVISOR``) because there is no auth in this PoC. In
production the role would come from the request context and flow
into the same ``assert_transition`` call from the domain layer.
"""

from src.domain.articles import (
    Article,
    ArticleDraft,
    ArticleStatus,
    ArticleSummary,
    ArticleUpdate,
    BookshelfRepository,
    ExternalArticleSource,
    ImportReport,
    assert_transition,
    find_stop_word,
)
from src.domain.articles.publication import (
    ArticlePublicationRejected,
    PipelineResult,
    PublicationContext,
    editorial_pipeline,
    submission_pipeline,
)
from src.domain.cognitive_layer import (
    AssistanceKind,
    CognitiveLayer,
    CognitiveRequest,
    CognitiveResponse,
)
from src.domain.errors import (
    ArticleNotFound,
    CognitiveOutputRefused,
    DomainError,
)
from src.domain.users import UserRole


async def articles_list(
    repository: BookshelfRepository,
) -> list[ArticleSummary]:
    return await repository.load_articles()


async def get_article(
    repository: BookshelfRepository,
    slug: str,
) -> Article:
    return await repository.article(slug)


async def create_article(
    repository: BookshelfRepository,
    draft: ArticleDraft,
) -> Article:
    """Create a new article in the DRAFT state.

    Renamed from ``publish_article`` (Parts 1-3): now that the
    lifecycle has a real PUBLISHED state, "publishing" no longer
    means "creating". A fresh row always lands in DRAFT.
    """

    draft.validate_policies()
    return await repository.add_article(draft)


async def update_article(
    repository: BookshelfRepository,
    slug: str,
    data: ArticleUpdate,
) -> Article:
    data.validate_policies()
    existing = await repository.article(slug)
    return await repository.update_article(existing.id, data)


async def delete_article(
    repository: BookshelfRepository,
    slug: str,
) -> None:
    await repository.delete_article(slug)


async def summarize_article(
    repository: BookshelfRepository,
    cognitive: CognitiveLayer,
    slug: str,
) -> CognitiveResponse:
    article = await repository.article(slug)
    return await _ask_and_enforce(
        cognitive,
        kind=AssistanceKind.SUMMARIZE,
        input_text=article.body,
    )


async def improve_grammar(
    repository: BookshelfRepository,
    cognitive: CognitiveLayer,
    slug: str,
    text: str,
) -> CognitiveResponse:
    article = await repository.article(slug)
    return await _ask_and_enforce(
        cognitive,
        kind=AssistanceKind.IMPROVE_GRAMMAR,
        input_text=text,
        context=article.body,
    )


async def suggest_title(
    repository: BookshelfRepository,
    cognitive: CognitiveLayer,
    slug: str,
) -> CognitiveResponse:
    article = await repository.article(slug)
    return await _ask_and_enforce(
        cognitive,
        kind=AssistanceKind.SUGGEST_TITLE,
        input_text=article.body,
    )


async def import_account_articles(
    repository: BookshelfRepository,
    source: ExternalArticleSource,
    account: str,
) -> ImportReport:
    imported = skipped = failed = 0

    async for draft in source.fetch(account):
        try:
            draft.validate_policies()
        except DomainError:
            failed += 1
            continue

        try:
            await repository.article(draft.slug)
        except ArticleNotFound:
            await repository.add_article(draft)
            imported += 1
        else:
            skipped += 1

    return ImportReport(
        source=source.kind,
        account=account,
        imported=imported,
        skipped=skipped,
        failed=failed,
    )


# ────────────────────────────────────────────────────────────
# Publication Lifecycle Use Cases
# ────────────────────────────────────────────────────────────
#
# Naming convention: each function name matches the verb on its HTTP
# endpoint. Each function hardcodes the role it represents (USER for
# author-side actions, SUPERVISOR for editorial actions). The role
# parameter flows into ``assert_transition`` (domain layer) — the
# same call shape an authed system would use, with the role coming
# from the request context instead of being a literal.


async def submit_article(
    repository: BookshelfRepository,
    cognitive: CognitiveLayer,
    slug: str,
) -> Article:
    """USER: DRAFT → SUBMITTED.

    Runs the submission pipeline (5 mechanical checks). The author is
    responsible for fixing every violation — the pipeline blocks the
    transition until the article is clean.
    """

    article = await repository.article(slug)
    assert_transition(article.status, ArticleStatus.SUBMITTED, UserRole.USER)

    pipeline = submission_pipeline()
    ctx = PublicationContext(repository=repository, cognitive=cognitive)
    result = await pipeline.run(article, ctx)

    if not result.passed:
        raise ArticlePublicationRejected(
            violations=[v.model_dump() for v in result.violations],
        )

    return await repository.transition(slug, ArticleStatus.SUBMITTED)


async def retract_article(
    repository: BookshelfRepository,
    slug: str,
) -> Article:
    """USER: SUBMITTED → DRAFT. No pipeline."""

    article = await repository.article(slug)
    assert_transition(article.status, ArticleStatus.DRAFT, UserRole.USER)
    return await repository.transition(slug, ArticleStatus.DRAFT)


async def pick_up_for_review(
    repository: BookshelfRepository,
    cognitive: CognitiveLayer,
    slug: str,
) -> tuple[Article, PipelineResult]:
    """SUPERVISOR: SUBMITTED → IN_REVIEW.

    Runs the editorial pipeline (2 cognitive checks). Findings are
    advisory — they are returned to the supervisor alongside the
    article so they can read the LLM's grammar/consistency notes
    before approving or rejecting. The transition is unconditional;
    the cognitive output never blocks.
    """

    article = await repository.article(slug)
    assert_transition(article.status, ArticleStatus.IN_REVIEW, UserRole.SUPERVISOR)

    pipeline = editorial_pipeline()
    ctx = PublicationContext(repository=repository, cognitive=cognitive)
    review_result = await pipeline.run(article, ctx)

    article = await repository.transition(slug, ArticleStatus.IN_REVIEW)
    return article, review_result


async def approve_article(
    repository: BookshelfRepository,
    slug: str,
) -> Article:
    """SUPERVISOR: IN_REVIEW → APPROVED → HIDDEN.

    Two transitions inside one transaction. APPROVED is the named
    supervisor decision; HIDDEN is the resting state the article
    sits in once approval is recorded. The persisted state after the
    transaction commits is always HIDDEN.
    """

    article = await repository.article(slug)
    assert_transition(article.status, ArticleStatus.APPROVED, UserRole.SUPERVISOR)
    await repository.transition(slug, ArticleStatus.APPROVED)
    assert_transition(
        ArticleStatus.APPROVED, ArticleStatus.HIDDEN, UserRole.SUPERVISOR
    )
    return await repository.transition(slug, ArticleStatus.HIDDEN)


async def reject_article(
    repository: BookshelfRepository,
    slug: str,
    reject_message: str,
) -> Article:
    """SUPERVISOR: IN_REVIEW → REJECTED.

    ``reject_message`` is required — the author needs to know why.
    The message is persisted on the article row and surfaced in the
    public response only while ``status == REJECTED``.
    """

    article = await repository.article(slug)
    assert_transition(article.status, ArticleStatus.REJECTED, UserRole.SUPERVISOR)
    return await repository.transition(
        slug, ArticleStatus.REJECTED, reject_message=reject_message
    )


async def revise_article(
    repository: BookshelfRepository,
    slug: str,
) -> Article:
    """USER: REJECTED → DRAFT.

    Clears ``reject_message`` (the repository enforces this — the
    field is meaningful only while the article is REJECTED).
    """

    article = await repository.article(slug)
    assert_transition(article.status, ArticleStatus.DRAFT, UserRole.USER)
    return await repository.transition(slug, ArticleStatus.DRAFT)


async def publish_article(
    repository: BookshelfRepository,
    slug: str,
) -> Article:
    """USER: HIDDEN → PUBLISHED.

    The terminal step. The author has had the HIDDEN article in their
    hands and chooses now to make it visible on the site.
    """

    article = await repository.article(slug)
    assert_transition(article.status, ArticleStatus.PUBLISHED, UserRole.USER)
    return await repository.transition(slug, ArticleStatus.PUBLISHED)


async def _ask_and_enforce(
    cognitive: CognitiveLayer,
    *,
    kind: AssistanceKind,
    input_text: str,
    context: str | None = None,
) -> CognitiveResponse:
    """Ask the cognitive layer and run article policies on the result."""

    request = CognitiveRequest(kind=kind, input=input_text, context=context)
    response = await cognitive.ask(request)

    word = find_stop_word(response.suggestion)
    if word is not None:
        raise CognitiveOutputRefused(
            f"suggestion contains forbidden word {word!r}"
        )

    return response
