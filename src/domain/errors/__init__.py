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
