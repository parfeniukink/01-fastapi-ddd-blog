"""Composition root — mount routers, build the app."""

from fastapi import FastAPI

from src.http.resources.articles import router as articles_router
from src.infrastructure.application import create_app


app: FastAPI = create_app(rest_routers=(articles_router,))
