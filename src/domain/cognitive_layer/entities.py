"""Cognitive-layer business shapes."""

from enum import StrEnum

from src.domain.base import DomainModel


class AssistanceKind(StrEnum):
    # Editorial assistance (Part 2 — interactive)
    SUMMARIZE = "summarize"
    IMPROVE_GRAMMAR = "improve_grammar"
    SUGGEST_TITLE = "suggest_title"
    # Publication-pipeline review (Part 4 — automated quality gate)
    REVIEW_GRAMMAR = "review_grammar"
    REVIEW_CONSISTENCY = "review_consistency"


class CognitiveRequest(DomainModel):
    kind: AssistanceKind
    input: str
    context: str | None = None


class CognitiveResponse(DomainModel):
    suggestion: str
    confidence: float | None = None
