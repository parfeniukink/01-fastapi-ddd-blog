# rest-ddd-fastapi-blog (iteration-02)

Read on blog: https://blog.parfeniukink.space/p/fastapi-ddd-blog

A small FastAPI project that demonstrates DDD dependency direction.

This branch is **Iteration 02** — the Part 1 baseline plus an AI assistant for
the writer, behind a `domain/cognitive_layer/` abstraction implemented with
[pydantic-ai](https://ai.pydantic.dev/).

## What changed (main → iteration-02)

- `src/domain/cognitive_layer/` — `CognitiveLayer` ABC, `CognitiveRequest` /
  `CognitiveResponse`, `AssistanceKind`, `PROMPTS`
- `src/domain/errors/__init__.py` — `CognitiveOutputRefused`,
  `CognitiveLayerUnavailable`
- `src/application/articles.py` — `summarize_article`, `improve_grammar`,
  `suggest_title`, plus the shared `_ask_and_enforce`
- `src/http/contracts/assistance.py` — `ActionRequest`, `ActionPublic`
- `src/http/resources/articles.py` — `POST /articles/{slug}/actions` dispatcher
- `src/infrastructure/pydantic_bindings.py` — `PydanticAICognitiveLayer`
- `src/infrastructure/application/error_handlers.py` — two new handlers + entries
- `src/tests/fakes/cognitive.py` and `src/tests/unit/test_cognitive.py`

## Install

```bash
pip install -e ".[dev]"
```

## Run

```bash
export OPENAI_API_KEY=...                # or another pydantic-ai provider
export ASSIST_MODEL=openai:gpt-4o-mini   # optional; default is openai:gpt-4o-mini
export DATABASE_URL=postgresql+asyncpg://blog:blog@localhost:5432/blog
uvicorn src.main:app --reload
```

## Test

```bash
pytest
```
