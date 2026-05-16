"""Transaction primitives — `transaction()` context manager and `@transactional`."""

from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from functools import wraps
from typing import ParamSpec, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from .dal import current_session


P = ParamSpec("P")
R = TypeVar("R")


@asynccontextmanager
async def transaction() -> AsyncIterator[AsyncSession]:
    """Run the enclosed block atomically.

    Opens a transaction if none is active; otherwise opens a SAVEPOINT
    so the inner block can roll back without aborting the outer one.
    """
    session = current_session()
    if session.in_transaction():
        async with session.begin_nested():
            yield session
    else:
        async with session.begin():
            yield session


def transactional(
    func: Callable[P, Awaitable[R]],
) -> Callable[P, Awaitable[R]]:
    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        async with transaction():
            return await func(*args, **kwargs)

    return wrapper
