# LearnFlow Auth — Backend (UC-1)

FastAPI + SQLAlchemy + PyJWT implementation of the UC-1 auth slice
(see `UC-1-requirements.md`). Matches the response shape and error codes the
frontend expects in `../frontend/src/api/authClient.ts`.

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
