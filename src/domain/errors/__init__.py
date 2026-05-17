"""Domain-layer errors.

The domain owns the vocabulary of failure. Outer layers translate
this vocabulary into transport-specific responses.
"""


class DomainError(Exception):
    pass


class ArticleNotFound(DomainError):
    def __init__(self, identifier: int | str) -> None:
        super().__init__(f"Article {identifier!r} was not found.")
        self.identifier = identifier


class ArticleContainsStopWord(DomainError):
    def __init__(self, *, field: str, word: str) -> None:
        super().__init__(
            f"Article {field!r} contains the forbidden word {word!r}."
        )
        self.field = field
        self.word = word


class ArticleSlugAlreadyExists(DomainError):
    def __init__(self, slug: str) -> None:
        super().__init__(f"Article with slug {slug!r} already exists.")
        self.slug = slug


class CognitiveOutputRefused(DomainError):
    """The cognitive layer declined to produce output."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"Cognitive layer refused: {reason}")
        self.reason = reason


class CognitiveLayerUnavailable(DomainError):
    """The cognitive layer was unreachable."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"Cognitive layer unavailable: {reason}")
        self.reason = reason


class ExternalSourceUnreachable(DomainError):
    """An external article source could not be reached."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"External source unreachable: {reason}")
        self.reason = reason


class ExternalSourceFormatChanged(DomainError):
    """An external article source returned an unexpected shape."""

    def __init__(self, reason: str) -> None:
        super().__init__(f"External source format changed: {reason}")
        self.reason = reason


class ArticleInvalidTransition(DomainError):
    """An article cannot move from `from_status` to `to_status` (by `role`).

    Carries the acting role too — the same transition may be illegal
    because of the source state, the target state, OR because the role
    is not the one that owns the transition. The error stays a single
    type with three fields rather than splitting into separate classes,
    so the error mapping is one entry.
    """

    def __init__(self, *, from_status: str, to_status: str, role: str) -> None:
        super().__init__(
            f"Role {role!r} cannot transition article from "
            f"{from_status!r} to {to_status!r}."
        )
        self.from_status = from_status
        self.to_status = to_status
        self.role = role


class ArticlePublicationRejected(DomainError):
    """The publication pipeline produced violations."""

    def __init__(self, violations: list[dict[str, object]]) -> None:
        super().__init__(
            f"Article failed publication pipeline ({len(violations)} violations)."
        )
        self.violations = violations
