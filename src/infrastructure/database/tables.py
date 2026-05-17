"""SQLAlchemy table definitions — persistence shape, not business shape.

The ``articles`` table shape illustrates a deliberate gap between
persistence and the HTTP contract:

- ``reject_message`` lives directly on the row. In production every
  state change typically gets logged to a dedicated audit table; for
  this PoC we keep just the most recent rejection note inline.
- The HTTP layer (``ArticlePublic``) masks ``reject_message`` unless
  the article is currently REJECTED. The DB invariant — only REJECTED
  rows ever carry a non-NULL ``reject_message`` — is enforced by the
  repository's ``transition`` method, not by a database constraint.
"""

from sqlalchemy import Date, Integer, MetaData, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    metadata = MetaData()


class ArticlesTable(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    author: Mapped[str] = mapped_column(String(120), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    summary: Mapped[str] = mapped_column(String(500), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    published_on: Mapped[Date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    reject_message: Mapped[str | None] = mapped_column(
        Text, nullable=True, default=None
    )
