"""Fixtures for unit tests."""

from datetime import date

import pytest

from src.domain.articles import ArticleDraft
from src.tests.fakes.articles import InMemoryArticlesRepository


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
