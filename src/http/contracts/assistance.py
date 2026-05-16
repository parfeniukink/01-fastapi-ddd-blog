"""Public shapes for /articles/{slug}/actions."""

from pydantic import Field

from src.http._base import PublicModel


class ActionRequest(PublicModel):
    # `input` is meaningful only for actions that take user-supplied text
    # (currently: improve_grammar). Empty strings are rejected at the
    # contract level via `min_length=1`.
    input: str | None = Field(default=None, min_length=1)


class ActionPublic(PublicModel):
    suggestion: str
    confidence: float | None = None
