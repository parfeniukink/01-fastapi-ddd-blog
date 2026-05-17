"""Articles HTTP resource — CRUD, actions, imports, publication lifecycle.

NOTE on auth: this PoC has no authentication and no users module. Every
endpoint is unprotected. The role attribution (USER vs SUPERVISOR) lives
in the application layer — each use case is bound to the role it
represents. In production the role would come from auth middleware
and the resource would forward it; here it is hardcoded per use case.

NOTE on naming: each publication endpoint is named for its verb
(``/submit``, ``/retract``, ``/review``, ``/approve``, ``/reject``,
``/revise``, ``/publish``). This is a deliberate move away from the
single ``/actions`` dispatcher introduced for editorial assistance in
Part 2 — verb endpoints survive growth, a generic ``/actions`` name
collides with every other "thing you do with an article". The Part 2
endpoint stays as-is for backwards compat; new ones follow this rule.
"""

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
from src.http.contracts.review import (
    CheckViolationPublic,
    RejectRequest,
    ReviewPickupPublic,
)
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
    article = await articles.create_article(repository, candidate)
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
    """Dispatch a writer-initiated AI assistance action.

    This is the Part 2 endpoint kept for backwards compat. The
    ``/actions`` name is too generic — see the module docstring.
    Publication endpoints (below) use verb names instead.
    """

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


# ────────────────────────────────────────────────────────────
# Publication Lifecycle Endpoints
# ────────────────────────────────────────────────────────────
# USER side:       /submit  /retract  /revise  /publish
# SUPERVISOR side: /review  /approve  /reject


@router.post("/{slug}/submit", status_code=status.HTTP_200_OK)
@transactional
async def article_submit(slug: str) -> ArticlePublic:
    """USER: DRAFT → SUBMITTED. Submission pipeline gates the transition."""

    repository = SqlAlchemyArticlesRepository()
    cognitive = PydanticAICognitiveLayer()
    article = await articles.submit_article(
        repository=repository,
        cognitive=cognitive,
        slug=slug,
    )
    return ArticlePublic.model_validate(article)


@router.post("/{slug}/retract", status_code=status.HTTP_200_OK)
@transactional
async def article_retract(slug: str) -> ArticlePublic:
    """USER: SUBMITTED → DRAFT. Author pulls the article back."""

    repository = SqlAlchemyArticlesRepository()
    article = await articles.retract_article(repository, slug)
    return ArticlePublic.model_validate(article)


@router.post("/{slug}/review", status_code=status.HTTP_200_OK)
@transactional
async def article_review(slug: str) -> ReviewPickupPublic:
    """SUPERVISOR: SUBMITTED → IN_REVIEW. Editorial pipeline runs advisory."""

    repository = SqlAlchemyArticlesRepository()
    cognitive = PydanticAICognitiveLayer()
    article, review_result = await articles.pick_up_for_review(
        repository=repository,
        cognitive=cognitive,
        slug=slug,
    )
    return ReviewPickupPublic(
        article=ArticlePublic.model_validate(article),
        editorial_notes=[
            CheckViolationPublic.model_validate(v, from_attributes=True)
            for v in review_result.violations
        ],
    )


@router.post("/{slug}/approve", status_code=status.HTTP_200_OK)
@transactional
async def article_approve(slug: str) -> ArticlePublic:
    """SUPERVISOR: IN_REVIEW → APPROVED → HIDDEN (two transitions, one tx)."""

    repository = SqlAlchemyArticlesRepository()
    article = await articles.approve_article(repository=repository, slug=slug)
    return ArticlePublic.model_validate(article)


@router.post("/{slug}/reject", status_code=status.HTTP_200_OK)
@transactional
async def article_reject(slug: str, body: RejectRequest) -> ArticlePublic:
    """SUPERVISOR: IN_REVIEW → REJECTED. `reject_message` required."""

    repository = SqlAlchemyArticlesRepository()
    article = await articles.reject_article(
        repository=repository,
        slug=slug,
        reject_message=body.reject_message,
    )
    return ArticlePublic.model_validate(article)


@router.post("/{slug}/revise", status_code=status.HTTP_200_OK)
@transactional
async def article_revise(slug: str) -> ArticlePublic:
    """USER: REJECTED → DRAFT. Clears the reject_message."""

    repository = SqlAlchemyArticlesRepository()
    article = await articles.revise_article(repository, slug)
    return ArticlePublic.model_validate(article)


@router.post("/{slug}/publish", status_code=status.HTTP_200_OK)
@transactional
async def article_publish(slug: str) -> ArticlePublic:
    """USER: HIDDEN → PUBLISHED. Terminal."""

    repository = SqlAlchemyArticlesRepository()
    article = await articles.publish_article(repository, slug)
    return ArticlePublic.model_validate(article)
