# rest-ddd-fastapi-blog (iteration-03)

A small FastAPI project that demonstrates DDD dependency direction.

This branch is **Iteration 03** — the Part 2 state plus inbound integrations.
One domain abstraction (`ExternalArticleSource`) sits in front of two
concrete adapters (`MediumArticleSource`, `RedditArticleSource`) that pull
posts from Medium RSS and Reddit JSON.

## What changed (iteration-02 → iteration-03)

- `src/domain/articles/inbound.py` — `ExternalSource` enum, `ImportReport`
  shape, `ExternalArticleSource` ABC (one file inside the existing aggregate)
- `src/domain/errors/__init__.py` — `ExternalSourceUnreachable` (→ 503) and
  `ExternalSourceFormatChanged` (→ 502)
- `src/application/articles.py` — `import_account_articles(repository, source, account)`
- `src/http/contracts/imports.py` — `ImportRequest` (`min_length=1` on account)
  and `ImportReportPublic`
- `src/http/resources/articles.py` — `POST /articles/imports?source=...` dispatcher
- `src/infrastructure/integrations/{medium.py, reddit.py}` — concrete adapters
  with their own URL templates, timeouts, and JSON / RSS parsing
- `src/infrastructure/application/error_handlers.py` — two new handlers + entries
- `src/tests/fakes/inbound.py` and `src/tests/unit/test_imports.py`

## Install

```bash
pip install -e ".[dev]"
```

## Run

```bash
export OPENAI_API_KEY=...
export DATABASE_URL=postgresql+asyncpg://blog:blog@localhost:5432/blog
uvicorn src.main:app --reload
```

## Test

```bash
pytest
```
