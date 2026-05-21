# rest-ddd-fastapi-blog

Read on blog: https://blog.parfeniukink.space/p/fastapi-ddd-blog

A small FastAPI project that demonstrates DDD dependency direction.

`main` is **Iteration 01** — CRUD + the dependency direction. The follow-on
branches (`iteration-02`, `iteration-03`, `iteration-04`) add an AI assistant,
inbound integrations, and internal domain growth (leads + papers). Diff
between any two branches to see what a given part adds.

## Goal

- `domain` contains business models, errors, and repository contracts
- `application` coordinates use cases against domain contracts
- `http` exposes REST endpoints and maps domain errors to status codes
- `infrastructure` implements persistence details
- `main.py` is the composition root that wires everything together
- tests construct the in-memory repository directly — no database required

## Install

```bash
pip install -e ".[dev]"
```

## Database assumptions

This example assumes PostgreSQL already exists and already has an `articles`
table that matches `src/infrastructure/database/tables.py`.

```bash
postgresql+asyncpg://blog:blog@localhost:5432/blog
```

Example minimal schema:

```sql
CREATE TABLE articles (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL UNIQUE,
    summary VARCHAR(500) NOT NULL,
    body TEXT NOT NULL,
    published_on DATE NOT NULL
);
```

## Run

```bash
export DATABASE_URL=postgresql+asyncpg://blog:blog@localhost:5432/blog
uvicorn src.main:app --reload
```

## Test

```bash
pytest
```
