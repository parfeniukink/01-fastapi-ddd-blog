"""Map domain errors onto standardized REST error responses.

This module is the single translation point between the domain's
failure vocabulary and the HTTP wire.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse

from src.domain.errors import (
    ArticleContainsStopWord,
    ArticleNotFound,
    ArticleSlugAlreadyExists,
    CognitiveLayerUnavailable,
    CognitiveOutputRefused,
    DomainError,
    ExternalSourceFormatChanged,
    ExternalSourceUnreachable,
)


async def article_not_found_handler(
    _: Request, exc: ArticleNotFound
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc), "identifier": exc.identifier},
    )


async def article_contains_stop_word_handler(
    _: Request, exc: ArticleContainsStopWord
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc), "field": exc.field, "word": exc.word},
    )


async def article_slug_already_exists_handler(
    _: Request, exc: ArticleSlugAlreadyExists
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc), "slug": exc.slug},
    )


async def cognitive_output_refused_handler(
    _: Request, exc: CognitiveOutputRefused
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": str(exc), "reason": exc.reason},
    )


async def cognitive_layer_unavailable_handler(
    _: Request, exc: CognitiveLayerUnavailable
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": str(exc), "reason": exc.reason},
    )


async def external_source_unreachable_handler(
    _: Request, exc: ExternalSourceUnreachable
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": str(exc), "reason": exc.reason},
    )


async def external_source_format_changed_handler(
    _: Request, exc: ExternalSourceFormatChanged
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": str(exc), "reason": exc.reason},
    )


ERROR_HANDLERS: tuple[tuple[type[DomainError], object], ...] = (
    (ArticleNotFound, article_not_found_handler),
    (ArticleContainsStopWord, article_contains_stop_word_handler),
    (ArticleSlugAlreadyExists, article_slug_already_exists_handler),
    (CognitiveOutputRefused, cognitive_output_refused_handler),
    (CognitiveLayerUnavailable, cognitive_layer_unavailable_handler),
    (ExternalSourceUnreachable, external_source_unreachable_handler),
    (ExternalSourceFormatChanged, external_source_format_changed_handler),
)
