"""Articles HTTP resource — CRUD, editorial actions, inbound imports."""

from fastapi import APIRouter, HTTPException, status

from src.application import articles
from src.domain.articles import ArticleDraft, ArticleUpdate, ExternalSource
from src.domain.cognitive_layer import AssistanceKind
from src.http.contracts.articles import (
    ArticleCreateRequest,
    ArticlePublic,
    ArticleSummaryPublic,
    ArticleUpdateRequest,
)
from src.http.contracts.assistance import ActionPublic, ActionRequest
from src.http.contracts.imports import ImportReportPublic, ImportRequest
from src.infrastructure.database.repositories.articles import (
    SqlAlchemyArticlesRepository,
)
from src.infrastructure.database.transaction import transactional
from src.infrastructure.integrations import (
    MediumArticleSource,
    RedditArticleSource,
)
from src.infrastructure.pydantic_bindings import PydanticAICognitiveLayer


router = APIRouter(prefix="/articles", tags=["Articles"])


@router.get("", status_code=status.HTTP_200_OK)
async def articles_list() -> list[ArticleSummaryPublic]:
    repository = SqlAlchemyArticlesRepository()
    result = await articles.articles_list(repository)
    return [ArticleSummaryPublic.model_validate(a) for a in result]


@router.get("/{slug}", status_code=status.HTTP_200_OK)
async def article_details(slug: str) -> ArticlePublic:
    repository = SqlAlchemyArticlesRepository()
    article = await articles.get_article(repository, slug)
    return ArticlePublic.model_validate(article)


@router.post("", status_code=status.HTTP_201_CREATED)
@transactional
async def article_create(body: ArticleCreateRequest) -> ArticlePublic:
    repository = SqlAlchemyArticlesRepository()
    candidate = ArticleDraft.model_validate(body, from_attributes=True)
    article = await articles.publish_article(repository, candidate)
    return ArticlePublic.model_validate(article)


@router.put("/{slug}", status_code=status.HTTP_200_OK)
@transactional
async def article_update(slug: str, body: ArticleUpdateRequest) -> ArticlePublic:
    repository = SqlAlchemyArticlesRepository()
    data = ArticleUpdate.model_validate(body, from_attributes=True)
    article = await articles.update_article(repository, slug, data)
    return ArticlePublic.model_validate(article)


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
@transactional
async def article_delete(slug: str) -> None:
    repository = SqlAlchemyArticlesRepository()
    await articles.delete_article(repository, slug)


@router.post("/{slug}/actions", status_code=status.HTTP_200_OK)
async def article_actions(
    slug: str,
    action: AssistanceKind,
    body: ActionRequest | None = None,
) -> ActionPublic:
    """Dispatch a writer-initiated action against an article."""
    repository = SqlAlchemyArticlesRepository()
    layer = PydanticAICognitiveLayer()

    match action:
        case AssistanceKind.SUMMARIZE:
            response = await articles.summarize_article(repository, layer, slug)

        case AssistanceKind.IMPROVE_GRAMMAR:
            if body is None or body.input is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="`input` is required for improve_grammar",
                )
            response = await articles.improve_grammar(
                repository, layer, slug, body.input,
            )

        case AssistanceKind.SUGGEST_TITLE:
            response = await articles.suggest_title(repository, layer, slug)

    return ActionPublic.model_validate(response)


@router.post("/imports", status_code=status.HTTP_200_OK)
@transactional
async def article_imports(
    body: ImportRequest,
    source: ExternalSource,
) -> ImportReportPublic:
    """Pull articles from `?source=<medium|reddit>` for `account`."""
    repository = SqlAlchemyArticlesRepository()

    match source:
        case ExternalSource.MEDIUM:
            adapter = MediumArticleSource()
        case ExternalSource.REDDIT:
            adapter = RedditArticleSource()

    report = await articles.import_account_articles(
        repository=repository,
        source=adapter,
        account=body.account,
    )
    return ImportReportPublic.model_validate(report)
