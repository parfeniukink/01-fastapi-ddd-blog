"""Fixtures for unit tests."""

from datetime import date

import pytest

from src.domain.articles import Article, ArticleDraft
from src.tests.fakes.articles import InMemoryArticlesRepository
from src.tests.fakes.cognitive import FakeCognitiveLayer


@pytest.fixture
def repository() -> InMemoryArticlesRepository:
    return InMemoryArticlesRepository(items=[])


@pytest.fixture
def sample_draft() -> ArticleDraft:
    return ArticleDraft(
        title="First post",
        slug="first-post",
        summary="A summary.",
        body="Hello.",
        published_on=date(2024, 1, 1),
    )


@pytest.fixture
def seeded_repository(sample_draft: ArticleDraft) -> InMemoryArticlesRepository:
    """Repository pre-loaded with one article (slug='first-post')."""
    return InMemoryArticlesRepository(
        items=[Article(id=1, **sample_draft.model_dump())]
    )


@pytest.fixture
def cognitive() -> FakeCognitiveLayer:
    return FakeCognitiveLayer(suggestion="Improved suggestion.")
