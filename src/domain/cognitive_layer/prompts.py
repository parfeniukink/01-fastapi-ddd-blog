"""Editorial prompts per `AssistanceKind` — domain knowledge."""

from .entities import AssistanceKind


PROMPTS: dict[AssistanceKind, str] = {
    AssistanceKind.SUMMARIZE: (
        "Summarize the following article in one or two sentences. "
        "Return only the summary."
    ),
    AssistanceKind.IMPROVE_GRAMMAR: (
        "Improve the grammar and clarity of the following text. "
        "Do not change the factual content. Return only the improved text."
    ),
    AssistanceKind.SUGGEST_TITLE: (
        "Suggest a short, clear title for the article below. "
        "Return only the title."
    ),
    AssistanceKind.REVIEW_GRAMMAR: (
        "Review the following article for grammar, spelling, and clarity issues. "
        "If there are no issues, return exactly 'CLEAN'. "
        "Otherwise, list each issue on its own line, prefixed with '- '. "
        "Be terse: one line per issue."
    ),
    AssistanceKind.REVIEW_CONSISTENCY: (
        "Review the following article for logical inconsistencies, factual "
        "contradictions, or claims that the article itself does not support. "
        "If there are no issues, return exactly 'CLEAN'. "
        "Otherwise, list each issue on its own line, prefixed with '- '."
    ),
}
