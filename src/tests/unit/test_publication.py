"""Publication lifecycle tests.

Covers: each check individually, both pipelines (submission gates,
editorial advises), all seven publication use cases, role enforcement
on the transition table, and the reject_message clearing invariant.
"""

from datetime import date

import pytest

from src.application import articles as articles_use_cases
from src.domain.articles import Article, ArticleStatus
from src.domain.articles.publication import (
    AuthorityCheck,
    CitationCheck,
    ConsistencyReviewCheck,
    GrammarReviewCheck,
    PublicationContext,
    StopWordsCheck,
    StructureCheck,
    editorial_pipeline,
    submission_pipeline,
)
from src.domain.articles import can_transition
from src.domain.errors import (
    ArticleInvalidTransition,
    ArticlePublicationRejected,
)
from src.domain.users import UserRole
from src.tests.fakes.cognitive import FakeCognitiveLayer


# ────────────────────────────────────────────────────────────
# Individual Mechanical Checks
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_authority_check_rejects_unknown_author(
    publishable_article, repository, cognitive_clean
) -> None:
    article = publishable_article.model_copy(update={"author": "stranger"})
    ctx = PublicationContext(repository=repository, cognitive=cognitive_clean)

    violations = await AuthorityCheck().run(article, ctx)

    assert len(violations) == 1
    assert violations[0].code == "authority"


@pytest.mark.asyncio
async def test_stop_words_check_flags_per_field(
    publishable_article, repository, cognitive_clean
) -> None:
    article = publishable_article.model_copy(
        update={
            "title": "Top 10 spam techniques",
            "summary": "A clickbait piece",
        }
    )
    ctx = PublicationContext(repository=repository, cognitive=cognitive_clean)

    violations = await StopWordsCheck().run(article, ctx)
    fields = {v.field for v in violations}

    assert {"title", "summary"} <= fields


@pytest.mark.asyncio
async def test_citation_check_requires_external_link(
    publishable_article, repository, cognitive_clean
) -> None:
    article = publishable_article.model_copy(update={"body": "no links here, sorry"})
    ctx = PublicationContext(repository=repository, cognitive=cognitive_clean)

    violations = await CitationCheck().run(article, ctx)

    assert violations[0].code == "citation"


# ────────────────────────────────────────────────────────────
# Submission Pipeline (Mechanical, Blocking)
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_submission_pipeline_collects_mechanical_violations(
    draft_article, repository, cognitive_clean
) -> None:
    pipeline = submission_pipeline()
    ctx = PublicationContext(repository=repository, cognitive=cognitive_clean)

    result = await pipeline.run(draft_article, ctx)
    codes = {v.code for v in result.violations}

    assert not result.passed
    assert {"structure", "citation"} <= codes


@pytest.mark.asyncio
async def test_submission_pipeline_passes_for_a_clean_article(
    publishable_article, repository, cognitive_clean
) -> None:
    pipeline = submission_pipeline()
    ctx = PublicationContext(repository=repository, cognitive=cognitive_clean)

    result = await pipeline.run(publishable_article, ctx)

    assert result.passed
    assert result.violations == []


# ────────────────────────────────────────────────────────────
# Editorial Pipeline (Cognitive, Advisory)
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_editorial_pipeline_grammar_returns_one_violation_per_line(
    publishable_article, repository
) -> None:
    canned = FakeCognitiveLayer(
        suggestion=(
            "- subject-verb agreement in paragraph 2\n"
            "- comma splice in paragraph 4"
        )
    )
    ctx = PublicationContext(repository=repository, cognitive=canned)

    violations = await GrammarReviewCheck().run(publishable_article, ctx)

    assert len(violations) == 2
    assert all(v.code == "grammar" for v in violations)


@pytest.mark.asyncio
async def test_editorial_pipeline_consistency_returns_no_violations_on_clean(
    publishable_article, repository, cognitive_clean
) -> None:
    ctx = PublicationContext(repository=repository, cognitive=cognitive_clean)

    violations = await ConsistencyReviewCheck().run(publishable_article, ctx)

    assert violations == []


# ────────────────────────────────────────────────────────────
# /submit Use Case
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_submit_transitions_clean_draft_to_submitted(
    publishable_article, repository, cognitive_clean
) -> None:
    await repository.add_article(publishable_article)

    result = await articles_use_cases.submit_article(
        repository=repository,
        cognitive=cognitive_clean,
        slug=publishable_article.slug,
    )

    assert result.status == ArticleStatus.SUBMITTED


@pytest.mark.asyncio
async def test_submit_raises_with_violations_when_pipeline_fails(
    draft_article, repository, cognitive_clean
) -> None:
    await repository.add_article(draft_article)

    with pytest.raises(ArticlePublicationRejected) as exc_info:
        await articles_use_cases.submit_article(
            repository=repository,
            cognitive=cognitive_clean,
            slug=draft_article.slug,
        )

    assert len(exc_info.value.violations) >= 1


# ────────────────────────────────────────────────────────────
# /retract Use Case
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_retract_returns_submitted_article_to_draft(
    publishable_article, repository, cognitive_clean
) -> None:
    await repository.add_article(publishable_article)
    await articles_use_cases.submit_article(
        repository=repository,
        cognitive=cognitive_clean,
        slug=publishable_article.slug,
    )

    result = await articles_use_cases.retract_article(
        repository=repository, slug=publishable_article.slug
    )

    assert result.status == ArticleStatus.DRAFT


# ────────────────────────────────────────────────────────────
# /review Use Case
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_review_transitions_to_in_review_with_editorial_notes(
    publishable_article, repository, cognitive_clean
) -> None:
    await repository.add_article(publishable_article)
    await articles_use_cases.submit_article(
        repository=repository,
        cognitive=cognitive_clean,
        slug=publishable_article.slug,
    )

    article, review_result = await articles_use_cases.pick_up_for_review(
        repository=repository,
        cognitive=cognitive_clean,
        slug=publishable_article.slug,
    )

    assert article.status == ArticleStatus.IN_REVIEW
    # cognitive_clean returns 'CLEAN' → no advisory notes
    assert review_result.passed
    assert review_result.violations == []


@pytest.mark.asyncio
async def test_review_does_not_block_on_cognitive_findings(
    publishable_article, repository, cognitive_clean
) -> None:
    """Editorial pipeline output is advisory — transition happens regardless."""
    await repository.add_article(publishable_article)
    await articles_use_cases.submit_article(
        repository=repository,
        cognitive=cognitive_clean,
        slug=publishable_article.slug,
    )
    noisy = FakeCognitiveLayer(suggestion="- many grammar issues found")

    article, review_result = await articles_use_cases.pick_up_for_review(
        repository=repository,
        cognitive=noisy,
        slug=publishable_article.slug,
    )

    assert article.status == ArticleStatus.IN_REVIEW
    assert not review_result.passed
    assert review_result.violations  # non-empty, but the transition still happened


# ────────────────────────────────────────────────────────────
# /approve Use Case
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_approve_collapses_through_approved_to_hidden(
    publishable_article, repository, cognitive_clean
) -> None:
    await repository.add_article(publishable_article)
    await articles_use_cases.submit_article(
        repository=repository,
        cognitive=cognitive_clean,
        slug=publishable_article.slug,
    )
    await articles_use_cases.pick_up_for_review(
        repository=repository,
        cognitive=cognitive_clean,
        slug=publishable_article.slug,
    )

    result = await articles_use_cases.approve_article(
        repository=repository, slug=publishable_article.slug
    )

    # The /approve transaction runs two transitions; the resting state is HIDDEN.
    assert result.status == ArticleStatus.HIDDEN


@pytest.mark.asyncio
async def test_approve_requires_in_review_status(
    publishable_article, repository
) -> None:
    await repository.add_article(publishable_article)
    with pytest.raises(ArticleInvalidTransition):
        await articles_use_cases.approve_article(
            repository=repository, slug=publishable_article.slug
        )


# ────────────────────────────────────────────────────────────
# /reject Use Case
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_reject_records_reject_message(
    publishable_article, repository, cognitive_clean
) -> None:
    await repository.add_article(publishable_article)
    await articles_use_cases.submit_article(
        repository=repository,
        cognitive=cognitive_clean,
        slug=publishable_article.slug,
    )
    await articles_use_cases.pick_up_for_review(
        repository=repository,
        cognitive=cognitive_clean,
        slug=publishable_article.slug,
    )

    result = await articles_use_cases.reject_article(
        repository=repository,
        slug=publishable_article.slug,
        reject_message="Citations are weak; please add primary sources.",
    )

    assert result.status == ArticleStatus.REJECTED
    assert result.reject_message == "Citations are weak; please add primary sources."


# ────────────────────────────────────────────────────────────
# /revise Use Case
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_revise_clears_reject_message(
    publishable_article, repository, cognitive_clean
) -> None:
    await repository.add_article(publishable_article)
    await articles_use_cases.submit_article(
        repository=repository,
        cognitive=cognitive_clean,
        slug=publishable_article.slug,
    )
    await articles_use_cases.pick_up_for_review(
        repository=repository,
        cognitive=cognitive_clean,
        slug=publishable_article.slug,
    )
    await articles_use_cases.reject_article(
        repository=repository,
        slug=publishable_article.slug,
        reject_message="needs work",
    )

    result = await articles_use_cases.revise_article(
        repository=repository, slug=publishable_article.slug
    )

    assert result.status == ArticleStatus.DRAFT
    assert result.reject_message is None


# ────────────────────────────────────────────────────────────
# /publish Use Case
# ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_publish_transitions_hidden_to_published(
    publishable_article, repository, cognitive_clean
) -> None:
    await repository.add_article(publishable_article)
    await articles_use_cases.submit_article(
        repository=repository,
        cognitive=cognitive_clean,
        slug=publishable_article.slug,
    )
    await articles_use_cases.pick_up_for_review(
        repository=repository,
        cognitive=cognitive_clean,
        slug=publishable_article.slug,
    )
    await articles_use_cases.approve_article(
        repository=repository, slug=publishable_article.slug
    )

    result = await articles_use_cases.publish_article(
        repository=repository, slug=publishable_article.slug
    )

    assert result.status == ArticleStatus.PUBLISHED


# ────────────────────────────────────────────────────────────
# Role-Aware Transition Table
# ────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "current, target, role, allowed",
    [
        # USER-owned transitions
        (ArticleStatus.DRAFT, ArticleStatus.SUBMITTED, UserRole.USER, True),
        (ArticleStatus.SUBMITTED, ArticleStatus.DRAFT, UserRole.USER, True),
        (ArticleStatus.REJECTED, ArticleStatus.DRAFT, UserRole.USER, True),
        (ArticleStatus.HIDDEN, ArticleStatus.PUBLISHED, UserRole.USER, True),
        # SUPERVISOR-owned transitions
        (ArticleStatus.SUBMITTED, ArticleStatus.IN_REVIEW, UserRole.SUPERVISOR, True),
        (ArticleStatus.IN_REVIEW, ArticleStatus.APPROVED, UserRole.SUPERVISOR, True),
        (ArticleStatus.IN_REVIEW, ArticleStatus.REJECTED, UserRole.SUPERVISOR, True),
        (ArticleStatus.APPROVED, ArticleStatus.HIDDEN, UserRole.SUPERVISOR, True),
        # Wrong role for an otherwise valid edge
        (ArticleStatus.DRAFT, ArticleStatus.SUBMITTED, UserRole.SUPERVISOR, False),
        (ArticleStatus.IN_REVIEW, ArticleStatus.APPROVED, UserRole.USER, False),
        (ArticleStatus.HIDDEN, ArticleStatus.PUBLISHED, UserRole.SUPERVISOR, False),
        # Illegal jumps regardless of role
        (ArticleStatus.DRAFT, ArticleStatus.PUBLISHED, UserRole.USER, False),
        (ArticleStatus.PUBLISHED, ArticleStatus.DRAFT, UserRole.USER, False),
    ],
)
def test_transition_table_enforces_role_ownership(
    current, target, role, allowed
) -> None:
    assert can_transition(current, target, role) is allowed
