"""FastAPI app factory.

Mounts routers, wires the request-scoped session middleware, and
registers the domain-to-REST error mappers. `main.py` hands in routers.
"""

from collections.abc import Iterable

from fastapi import APIRouter, FastAPI
from starlette.middleware.base import BaseHTTPMiddleware

from src.infrastructure.database.dal import session_scope

from .error_handlers import ERROR_HANDLERS


class DatabaseSessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        async with session_scope():
            return await call_next(request)


def create_app(*, rest_routers: Iterable[APIRouter]) -> FastAPI:
    app = FastAPI()
    app.add_middleware(DatabaseSessionMiddleware)
    for router in rest_routers:
        app.include_router(router)
    for exc_type, handler in ERROR_HANDLERS:
        app.add_exception_handler(exc_type, handler)
    return app
