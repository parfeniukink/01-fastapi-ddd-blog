"""Articles HTTP resource — CRUD, no business logic.

The session is request-scoped via `DatabaseSessionMiddleware`, so
route handlers do not declare `Depends(get_session)`. The repository
picks up the current session through `current_session()` inside
`SqlAlchemyDAL`.
"""

from fastapi import APIRouter, status

from src.application import articles
from src.domain.articles import ArticleDraft, ArticleUpdate
from src.http.contracts.articles import (
    ArticleCreateRequest,
    ArticlePublic,
    ArticleSummaryPublic,
    ArticleUpdateRequest,
)
from src.infrastructure.database.repositories.articles import (
    SqlAlchemyArticlesRepository,
)
from src.infrastructure.database.transaction import transactional


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
