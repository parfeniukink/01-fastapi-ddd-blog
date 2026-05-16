"""Database engine, per-request session scope, and the DAL base class.

The project assumes the database already exists.
The session is request-scoped through `DatabaseSessionMiddleware` (in
`infrastructure/application/factory.py`), which opens `session_scope()`
and seeds the `ContextVar`. Repository constructors read it via
`current_session()` — no `Depends(get_session)` in routes.

`SqlAlchemyDAL` owns the per-request session and exposes only what a
repository should touch — `session` for building statements and
`flush()` for pushing pending changes inside the current transaction.
"""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from contextvars import ContextVar

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://blog:blog@localhost:5432/blog",
)


_engine = create_async_engine(DATABASE_URL, future=True)
_session_factory = async_sessionmaker(_engine, expire_on_commit=False)


# Per-task pointer to the session bound to the current request.
_session_var: ContextVar[AsyncSession | None] = ContextVar(
    "_session_var", default=None
)


def current_session() -> AsyncSession:
    session = _session_var.get()
    if session is None:
        raise RuntimeError(
            "No active session. `current_session()` must run inside a "
            "request scoped by `session_scope()`."
        )
    return session


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """Open a session, bind it to the current task, and tear it down."""
    async with _session_factory() as session:
        token = _session_var.set(session)
        try:
            yield session
        finally:
            _session_var.reset(token)


class SqlAlchemyDAL:
    def __init__(self, session: AsyncSession | None = None) -> None:
        self._session = session or current_session()

    @property
    def session(self) -> AsyncSession:
        return self._session

    async def flush(self) -> None:
        await self._session.flush()
