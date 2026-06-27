# LearnFlow Auth — Backend (UC-1)

FastAPI + SQLAlchemy + PyJWT implementation of the UC-1 auth slice
(see `UC-1-requirements.md`). Matches the response shape and error codes the
frontend expects in `../frontend/src/api/authClient.ts`.

## UC-1: Authentication

UC-1 is the **register + login** slice of LearnFlow's auth module — enough for a
learner to create an account and obtain the tokens that authorize every other
call. It is intentionally narrow: the surrounding flows (refresh, logout, email
verification, password-reset confirmation) are designed for but not built here.

**What UC-1 delivers**

- **Register** (`POST /auth/register`) — create an account from name + email +
  password. Emails are unique and case-insensitive; passwords must pass the
  complexity policy and are stored only as bcrypt hashes. New accounts are
  `ACTIVE` in dev or `PENDING_VERIFICATION` when `REGISTER_ACTIVE=false`.
- **Login** (`POST /auth/login`) — exchange credentials for a short-lived JWT
  access token plus a long-lived refresh token (only the refresh token's hash is
  persisted). Issued JWTs embed `token_version` so a future password reset can
  invalidate them in bulk.
- **Current user** (`GET /auth/me`) — return the caller's profile from the bearer
  token; the validation seam (`get_current_user`) already checks signature,
  expiry, `token_version`, and account status.
- **Password-reset request** (`POST /auth/password-reset/request`) — an
  enumeration-safe `202` stub that the full reset flow will build on.

**Security properties baked into UC-1**

- **Enumeration-safe** login and password-reset: identical responses (and a
  constant-time dummy hash on unknown emails) so neither endpoint reveals which
  emails are registered.
- **Brute-force lockout**: 5 failed logins within 10 minutes lock the account for
  15 minutes (`429`); a correct login clears the counter.
- **Bounded work per request**: passwords are capped at 72 bytes (bcrypt's limit)
  to remove a CPU-exhaustion vector.
- **Algorithm-pinned JWTs**: the verifier only accepts the configured algorithm,
  rejecting `none` and unexpected algs.

**API contract / OpenAPI.** Every endpoint — and in particular `/auth/register`
and `/auth/login` — fully describes its success and error responses (status
codes, bodies, and examples) in the generated OpenAPI document. Browse it live at
`/docs` (Swagger UI) or `/redoc`, fetch the raw spec at `/openapi.json`, or read
the committed snapshot at [`../docs/openapi.json`](../docs/openapi.json).
Regenerate that snapshot after changing any endpoint or schema:

```bash
cd backend
python -m scripts.export_openapi      # writes ../docs/openapi.json
```

## Stack & decisions

- **DB:** SQLite for dev (`sqlite:///./learnflow.db`), Postgres for prod — switch via `DATABASE_URL`.
- **Hashing:** `pwdlib` with bcrypt.
- **JWT:** PyJWT, **HS256** by default, **RS256-ready** (set `JWT_ALGORITHM=RS256` + PEM key paths).
- **Lockout:** per-user (named) — 5 failed logins / 10 min → locked 15 min → `429`.
- **Register:** creates `ACTIVE` users in dev (`REGISTER_ACTIVE=true`); flip to `false` for the `PENDING_VERIFICATION` + email-verify flow.

## Endpoints

| Method | Path | Success | Notes |
| ------ | ---- | ------- | ----- |
| `POST` | `/auth/register` | `201 {message}` | `409` on duplicate email |
| `POST` | `/auth/login` | `200 {access_token, refresh_token, token_type}` | `401` invalid · `429` locked · `403` not-active |
| `POST` | `/auth/password-reset/request` | `202 {message}` | enumeration-safe stub (no email yet) |
| `GET`  | `/auth/me` | `200 {id,email,name,role,status}` | requires `Authorization: Bearer <token>` |

Out of scope here (UC-1 lists them, but this slice is register+login): `/auth/refresh`,
`/auth/logout`, `/auth/verify-email`, `/auth/password-reset/confirm`, real email dispatch.
Seams are in place: refresh tokens are persisted (hashed) and `token_version` is in the JWT.

## Run

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # optional; defaults work for dev

alembic upgrade head            # create the SQLite schema
uvicorn app.main:app --reload   # http://localhost:8000  (docs at /docs)
```

Then point the frontend at it: set `VITE_API_BASE=http://localhost:8000` in
`../frontend/.env` and restart `npm run dev`.

## Smoke test

```bash
# register
curl -s -XPOST localhost:8000/auth/register -H 'content-type: application/json' \
  -d '{"name":"Priya","email":"priya@example.com","password":"Password1!"}'

# login -> tokens
curl -s -XPOST localhost:8000/auth/login -H 'content-type: application/json' \
  -d '{"email":"priya@example.com","password":"Password1!"}'

# current user
curl -s localhost:8000/auth/me -H "Authorization: Bearer <access_token>"
```
