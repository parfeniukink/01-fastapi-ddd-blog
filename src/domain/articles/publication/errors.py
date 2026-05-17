"""Publication-specific re-export of the domain error.

Kept here as a thin re-export so importing from
`src.domain.articles.publication` is enough for the use case.
"""

from src.domain.errors import ArticlePublicationRejected

__all__ = ["ArticlePublicationRejected"]
