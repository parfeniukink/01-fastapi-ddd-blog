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
}
