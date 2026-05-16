"""Article use cases — CRUD, editorial actions, inbound imports.

CRUD and editorial actions hang off the same article aggregate.
`import_account_articles` is the Part 3 use case — it iterates an
`ExternalArticleSource`, runs the article aggregate's policies on
each draft, and persists through the existing repository.
"""

from src.domain.articles import (
    Article,
    ArticleDraft,
    ArticleSummary,
    ArticleUpdate,
    BookshelfRepository,
    ExternalArticleSource,
    ImportReport,
)
from src.domain.articles.policies import find_stop_word
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


async def articles_list(
    repository: BookshelfRepository,
) -> list[ArticleSummary]:
    return await repository.load_articles()


async def get_article(
    repository: BookshelfRepository,
    slug: str,
) -> Article:
    return await repository.article(slug)


async def publish_article(
    repository: BookshelfRepository,
    draft: ArticleDraft,
) -> Article:
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
    """Pull articles from `source` for `account` and persist them.

    Each fetched draft is validated against the article aggregate's
    own policies. Drafts whose slug already exists are skipped;
    drafts that fail domain validation are counted as failed; the
    rest go through `add_article`.
    """
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
