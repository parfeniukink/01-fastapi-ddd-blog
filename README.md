# rest-ddd-fastapi-blog (iteration-04)

A small FastAPI project that demonstrates DDD dependency direction.

This branch is **Iteration 04** — the Part 3 state plus an internal
domain growth: a role-aware article publication lifecycle with a
seven-state machine, a split publication pipeline (mechanical gates
submission, cognitive advises the supervisor on review), and a
deliberate persistence-shape vs HTTP-contract distinction for the
``reject_message`` field.

## Disclaimer (no auth, no users persistence)

There is no authentication and no persisted users in this PoC. Every
endpoint is unprotected. The role model lives in the domain only —
``UserRole.USER`` and ``UserRole.SUPERVISOR`` exist so the lifecycle
can express WHICH role owns WHICH transition, but every use case
hardcodes the role it represents because no auth layer injects one.
In production the role would come from auth middleware and flow into
the same ``can_transition`` check.

## What changed (iteration-03 → iteration-04)

### New domain module — users

- `src/domain/users/roles.py` — `UserRole` enum (`USER`, `SUPERVISOR`)

### Article lifecycle (seven states, role-aware transitions)

- `src/domain/articles/policies.py` — content rules (stop words) and
  the lifecycle rules now live in one file. Adds `ArticleStatus` enum
  with seven values (`DRAFT`, `SUBMITTED`, `IN_REVIEW`, `APPROVED`,
  `HIDDEN`, `REJECTED`, `PUBLISHED`), `ALLOWED_TRANSITIONS` keyed on
  the current status with `(target_status, role)` tuples,
  `can_transition(current, target, role)` (boolean), and
  `assert_transition(current, target, role)` which raises
  `ArticleInvalidTransition`. The use cases call `assert_transition`
  directly — no application-layer wrapper.

```
              USER                          SUPERVISOR                          USER
DRAFT ──submit─► SUBMITTED ──review─► IN_REVIEW ──approve─► APPROVED ──(auto)─► HIDDEN
  ▲               │   ▲                  │   │                                   │
  │  retract      │   │                  │   │ reject                            │
  └───────────────┘   │                  │   ▼                                   │ publish
        USER          │                  │  REJECTED ────revise (USER)──► DRAFT  │
                      │                  │                                       ▼
                      └──────────────────┘                                  PUBLISHED
```

`HIDDEN` is technically optional — `APPROVED` could move straight to
`PUBLISHED`. We keep it because it makes role ownership explicit:
`HIDDEN` and `REJECTED` are the two bridge states that hand control
back to the opposite party. The cost of one extra enum value buys a
much more transparent business contract.

### Application — publication use cases

- `src/application/articles.py` — renamed legacy `publish_article` →
  `create_article` (a new article lands in DRAFT, "create" is the
  honest verb). The name `publish_article` now belongs to the
  HIDDEN → PUBLISHED transition. New use cases (one per HTTP verb):
  - `submit_article` (USER, DRAFT → SUBMITTED, gates on submission_pipeline)
  - `retract_article` (USER, SUBMITTED → DRAFT)
  - `pick_up_for_review` (SUPERVISOR, SUBMITTED → IN_REVIEW, runs
    editorial_pipeline advisory)
  - `approve_article` (SUPERVISOR, IN_REVIEW → APPROVED → HIDDEN in
    one transaction)
  - `reject_article` (SUPERVISOR, IN_REVIEW → REJECTED, requires
    `reject_message`)
  - `revise_article` (USER, REJECTED → DRAFT, clears `reject_message`)
  - `publish_article` (USER, HIDDEN → PUBLISHED)

### Publication pipeline (split)

- `src/domain/articles/publication/pipeline.py` — two factories:
  - `submission_pipeline()` — 5 mechanical checks. Blocks `/submit`.
  - `editorial_pipeline()` — 2 cognitive checks. Advisory on `/review`;
    findings are returned to the supervisor, never blocking.

### HTTP — verb endpoints (not /actions)

- `src/http/resources/articles.py` — 7 publication endpoints, one per
  verb: `/submit /retract /review /approve /reject /revise /publish`.
  Deliberate move away from Part 2's single `/actions` dispatcher,
  whose name turned out to be too generic once more article-level
  actions arrived.

### HTTP contracts — persistence shape vs contract shape

- `src/http/contracts/review.py` — `RejectRequest` (single field
  `reject_message`), `CheckViolationPublic`, and `ReviewPickupPublic`
  (the `/review` response carries the article AND the editorial
  pipeline's advisory notes).
- `src/http/contracts/articles.py` — `ArticlePublic` now has a
  `reject_message: str | None` field with a `@model_serializer` that
  drops the field unless the article's `status == REJECTED`. The DB
  column is always present; the public contract masks it. One field,
  two shapes, depending on who's asking.

### Persistence

- `src/infrastructure/database/tables.py` — `last_review` JSON column
  removed; `reject_message` Text column added. (A real system would
  log every state change to a separate audit table. We deliberately
  keep just the most recent rejection note inline to demonstrate the
  contrast between DB shape and contract shape.)
- `src/infrastructure/database/repositories/articles.py` — `transition`
  enforces `reject_message is not None ↔ status is REJECTED`; any
  transition to a non-REJECTED state clears the column. The invariant
  lives in the repository so use cases can stay terse.

### Errors

- `src/domain/errors/__init__.py` — `ArticleInvalidTransition` gains a
  `role` field. The error message includes the role so the response
  tells the caller WHY the transition was illegal (wrong source state,
  wrong target, or wrong role).

### Tests

- `src/tests/unit/test_publication.py` — rewritten end-to-end. Covers
  the individual mechanical checks, both pipelines, the seven use
  cases, the `reject_message`-clearing invariant on `/revise`, and a
  parametrized table of role-ownership cases.

### Removed

- `src/domain/articles/lifecycle.py` — content merged into
  `policies.py` (lifecycle and content rules share a file because
  both answer the same question for the use case).
- `src/domain/articles/publication/review.py` — the `SupervisorReview`
  value object and the `ReviewDecision` enum are gone. The new
  lifecycle stores at most the most recent `reject_message`. A
  per-decision audit log would belong in a dedicated table.

## Install

```bash
pip install -e ".[dev]"
```

## Run

```bash
export OPENAI_API_KEY=...
export ASSIST_MODEL=openai:gpt-4o-mini
export DATABASE_URL=postgresql+asyncpg://blog:blog@localhost:5432/blog
uvicorn src.main:app --reload
```

## Test

```bash
pytest
```
