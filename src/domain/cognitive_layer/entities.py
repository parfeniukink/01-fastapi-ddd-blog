"""Cognitive-layer business shapes."""

from enum import StrEnum

from src.domain.base import DomainModel


class AssistanceKind(StrEnum):
    SUMMARIZE = "summarize"
    IMPROVE_GRAMMAR = "improve_grammar"
    SUGGEST_TITLE = "suggest_title"


class CognitiveRequest(DomainModel):
    kind: AssistanceKind
    input: str
    context: str | None = None


class CognitiveResponse(DomainModel):
    suggestion: str
    confidence: float | None = None
