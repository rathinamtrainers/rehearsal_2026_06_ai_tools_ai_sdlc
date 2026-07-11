# AGENTS.md — LearnFlow project context for AI coding agents

This file gives terminal coding agents (Antigravity CLI / `agy`, and any other) the
context they need to work in this repo in the existing house style. Read it before
planning or editing. Prefer matching the patterns already in `backend/app/` over
introducing new ones.

## What this project is

**LearnFlow** — a Learning Management System (LMS). This repo currently ships **UC-1
(User Registration & Authentication)** end-to-end. New features are added as thin
vertical slices on top of the existing auth foundation.

- **Backend:** Python **3.13** · FastAPI · SQLAlchemy 2.0 (sync) · Alembic · Pydantic v2 · PyJWT · pwdlib[bcrypt]
- **Frontend:** React 19 + TypeScript + Vite (in `frontend/`)
- **DB:** SQLite in dev (`sqlite:///./learnflow.db`), Postgres in prod (psycopg2)
- **Tests:** pytest (suite in `backend/tests/`)
- **Lint:** ruff

## Repository layout (backend)

```
backend/
  app/
    main.py            # FastAPI app; CORS; includes routers; /health
    config.py          # pydantic-settings Settings; `settings` singleton; env/.env
    database.py        # engine, SessionLocal, DeclarativeBase `Base`, get_db() dependency
    models.py          # SQLAlchemy ORM models (User, RefreshToken, enums)
    schemas.py         # Pydantic v2 request/response models
    security.py        # password hashing + JWT create/decode
    deps.py            # auth dependencies: get_current_user, CurrentUser
    routers/
      auth.py          # /auth/* endpoints
  alembic/versions/    # migrations
  tests/               # pytest; conftest.py provides fixtures
  scripts/export_openapi.py
```

## Conventions to follow (match these exactly)

### Models (`app/models.py`)
- Use SQLAlchemy 2.0 typed style: `Mapped[...]` + `mapped_column(...)`. Base is
  `DeclarativeBase` from `app.database` (`from app.database import Base`).
- Primary keys are **string UUIDs**: `Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)`.
- Timestamps are timezone-aware; use the existing `utcnow()` helper and
  `DateTime(timezone=True)`. Reuse `ensure_aware()` when comparing values read back from SQLite.
- Enums use `Enum(SomeEnum, native_enum=False, length=...)` (string enums subclassing `str, enum.Enum`).
- Foreign keys to users: `ForeignKey("users.id", ondelete="CASCADE")`.

### Schemas (`app/schemas.py`)
- Pydantic **v2**. Keep request and response models separate.
- **Never serialize secrets or answer keys.** For any model-with-a-correct-answer
  (e.g. a quiz question), the *read* schema must omit the correct-answer field —
  keep it server-side only.

### Routers (`app/routers/`)
- One `APIRouter(prefix="/<feature>", tags=["<feature>"])` per feature; include it in
  `app/main.py` via `app.include_router(...)`.
- Type the DB session as `DbSession = Annotated[Session, Depends(get_db)]`.
- Document status codes in the `responses={...}` block like `auth.py` does, and give
  every endpoint a docstring describing success + failure modes.

### Auth (reuse, do not reinvent)
- Protect endpoints by depending on the existing **`CurrentUser`** from `app.deps`
  (`from app.deps import CurrentUser`), which resolves the JWT bearer token to a
  `User` (checks signature, expiry, `token_version`, and `ACTIVE` status). Example:
  `def submit(payload: X, user: CurrentUser, db: DbSession): ...`.
- Do **not** write new token-parsing logic. `OAuth2PasswordBearer(tokenUrl="auth/login")`.

### Migrations
- Every model change needs an Alembic migration in `backend/alembic/versions/`.
  Generate with `alembic revision --autogenerate -m "<msg>"`, review it, then
  `alembic upgrade head`. Do not hand-edit the DB.

### Tests (`backend/tests/`)
- pytest. Use the fixtures in `conftest.py` (test client + isolated DB). Cover the
  happy path, the auth-required path (401 when unauthenticated), and edge cases.
- Run with `pytest -q` from `backend/`.

## Common commands (run from `backend/`)

```bash
alembic upgrade head                         # apply migrations
uvicorn app.main:app --reload --port 8000    # run the API (Swagger at /docs)
pytest -q                                     # run tests
ruff check .                                  # lint
```

## Guardrails
- Keep changes scoped to the feature slice being built; don't refactor unrelated code.
- Never commit secrets. `.env` is git-ignored; config comes from `app/config.py`.
- Show a plan before multi-file edits; make changes reviewable diff-by-diff.
