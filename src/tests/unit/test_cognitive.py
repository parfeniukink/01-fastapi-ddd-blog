import pytest

from src.application import articles as articles_use_cases
from src.domain.cognitive_layer import AssistanceKind
from src.domain.errors import ArticleNotFound, CognitiveOutputRefused
from src.tests.fakes.cognitive import FakeCognitiveLayer


@pytest.mark.asyncio
async def test_summarize_article_uses_article_body_as_input(
    seeded_repository, cognitive
) -> None:
    response = await articles_use_cases.summarize_article(
        seeded_repository, cognitive, slug="first-post",
    )

    assert response.suggestion == "Improved suggestion."
    assert cognitive.calls[0].kind == AssistanceKind.SUMMARIZE
    assert cognitive.calls[0].input == "Hello."


@pytest.mark.asyncio
async def test_improve_grammar_uses_user_text_and_article_context(
    seeded_repository, cognitive
) -> None:
    await articles_use_cases.improve_grammar(
        seeded_repository,
        cognitive,
        slug="first-post",
        text="This is the paragraph to fix.",
    )

    assert cognitive.calls[0].kind == AssistanceKind.IMPROVE_GRAMMAR
    assert cognitive.calls[0].input == "This is the paragraph to fix."
    assert cognitive.calls[0].context == "Hello."


@pytest.mark.asyncio
async def test_suggest_title_uses_article_body(
    seeded_repository, cognitive
) -> None:
    await articles_use_cases.suggest_title(
        seeded_repository, cognitive, slug="first-post",
    )

    assert cognitive.calls[0].kind == AssistanceKind.SUGGEST_TITLE
    assert cognitive.calls[0].input == "Hello."


@pytest.mark.asyncio
async def test_actions_raise_when_article_is_missing(
    repository, cognitive
) -> None:
    with pytest.raises(ArticleNotFound):
        await articles_use_cases.summarize_article(
            repository, cognitive, slug="does-not-exist",
        )


@pytest.mark.asyncio
async def test_action_rejects_suggestion_with_stop_words(
    seeded_repository,
) -> None:
    """Article policies apply to AI output too."""
    bad = FakeCognitiveLayer(suggestion="A clickbait headline.")
    with pytest.raises(CognitiveOutputRefused):
        await articles_use_cases.suggest_title(
            seeded_repository, bad, slug="first-post",
        )
