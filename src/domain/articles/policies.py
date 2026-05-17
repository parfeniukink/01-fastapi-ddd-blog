"""Article domain policies — content rules and lifecycle rules.

Two concerns live in one file because both answer the same question
from the use case's point of view: "is this move editorially valid?"

- **Content policies** (`find_stop_word`) constrain *what* the text
  contains.
- **Lifecycle policies** (`ArticleStatus`, `ALLOWED_TRANSITIONS`,
  `can_transition`, `assert_transition`) constrain *who* can move
  the article *where*.

The use cases call these as plain functions; the rule definitions
live here and nowhere else.
"""

from enum import StrEnum

from src.domain.errors import ArticleInvalidTransition
from src.domain.users import UserRole


# ────────────────────────────────────────────────────────────
# Content Policies
# ────────────────────────────────────────────────────────────


STOP_WORDS: frozenset[str] = frozenset({"spam", "clickbait", "scam"})


def find_stop_word(text: str) -> str | None:
    """Return the first stop word found in `text`, or None if clean."""

    lowered = text.lower()
    for word in STOP_WORDS:
        if word in lowered:
            return word
    return None


# ────────────────────────────────────────────────────────────
# Lifecycle Policies
# ────────────────────────────────────────────────────────────


class ArticleStatus(StrEnum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    HIDDEN = "hidden"
    REJECTED = "rejected"
    PUBLISHED = "published"


# (target_status, role_allowed_to_perform_the_transition)
Transition = tuple[ArticleStatus, UserRole]


ALLOWED_TRANSITIONS: dict[ArticleStatus, frozenset[Transition]] = {
    ArticleStatus.DRAFT: frozenset({
        (ArticleStatus.SUBMITTED, UserRole.USER),
    }),
    ArticleStatus.SUBMITTED: frozenset({
        (ArticleStatus.DRAFT, UserRole.USER),
        (ArticleStatus.IN_REVIEW, UserRole.SUPERVISOR),
    }),
    ArticleStatus.IN_REVIEW: frozenset({
        (ArticleStatus.APPROVED, UserRole.SUPERVISOR),
        (ArticleStatus.REJECTED, UserRole.SUPERVISOR),
    }),
    ArticleStatus.APPROVED: frozenset({
        (ArticleStatus.HIDDEN, UserRole.SUPERVISOR),
    }),
    ArticleStatus.HIDDEN: frozenset({
        (ArticleStatus.PUBLISHED, UserRole.USER),
    }),
    ArticleStatus.REJECTED: frozenset({
        (ArticleStatus.DRAFT, UserRole.USER),
    }),
    ArticleStatus.PUBLISHED: frozenset(),
}


def can_transition(
    current: ArticleStatus,
    target: ArticleStatus,
    role: UserRole,
) -> bool:
    """True if `role` may move an article from `current` to `target`."""

    return (target, role) in ALLOWED_TRANSITIONS[current]


def assert_transition(
    current: ArticleStatus,
    target: ArticleStatus,
    role: UserRole,
) -> None:
    """Raise `ArticleInvalidTransition` if the transition is not allowed."""

    if not can_transition(current, target, role):
        raise ArticleInvalidTransition(
            from_status=current.value,
            to_status=target.value,
            role=role.value,
        )
