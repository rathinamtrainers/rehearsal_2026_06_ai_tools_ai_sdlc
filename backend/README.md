# LearnFlow — Auth Backend (UC-1)

FastAPI + SQLAlchemy 2.0 + JWT. Implements the **register + login** slice of
[`UC-1-requirements.md`](./UC-1-requirements.md), serving the contract the React
client in [`../frontend/src/api/auth.ts`](../frontend/src/api/auth.ts) already expects.

- **Audience:** engineers running/extending the LearnFlow auth service.
- **Identity model:** email is the sole identifier — no username, no social/SSO.
- **This iteration:** `POST /auth/register`, `POST /auth/login`, a protected
  `GET /auth/me`, JWT issuance (HS256), pwdlib/bcrypt hashing, and real account
  lockout. Refresh-token persistence, `/auth/refresh`, logout, password reset, and
  email verification are **deferred** (see *Out of scope*).

## Run it

```bash
cd backend
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # defaults run on SQLite, zero infra
alembic upgrade head            # creates learnflow.db
uvicorn app.main:app --reload --port 8000   # http://localhost:8000/docs
pytest -q                       # run the test suite
```

Point at Postgres 17 in prod by setting `DATABASE_URL` (and a real `JWT_SECRET`):

```bash
DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/learnflow
```

## API contract

| Method | Path | Body | Success | Errors |
| ------ | ---- | ---- | ------- | ------ |
| `POST` | `/auth/register` | `{name, email, password}` | `201` `{message, status}` | `409` duplicate · `422` weak password |
| `POST` | `/auth/login` | `{email, password}` | `200` `{access_token, refresh_token, token_type}` | `401` bad creds · `429` locked · `403` inactive |
| `GET`  | `/auth/me` | — (Bearer token) | `200` `{id, email, full_name, role, status}` | `401` |

Access-token claims (AC-AUTH-07): `sub` (user UUID), `role`, `iat`, `exp` (iat+15m),
`jti`, `tv` (token_version).

## Login decision flow

```mermaid
flowchart TD
    A[POST /auth/login] --> B{user exists?}
    B -- no --> D[dummy-hash verify] --> E[401 Invalid email or password]
    B -- yes --> F{locked_until in future?}
    F -- yes --> G[429 + Retry-After · skip password]
    F -- no --> H{password correct?}
    H -- no --> I[failed_attempts++] --> J{>= 5?}
    J -- yes --> K[lock 15m · status LOCKED] --> E
    J -- no --> E
    H -- yes --> L[reset attempts · last_login_at=now] --> M[200 access+refresh]

    classDef bad fill:#fef2f2,stroke:#dc2626,color:#0f172a;
    classDef lock fill:#fffbeb,stroke:#d97706,color:#0f172a;
    classDef ok fill:#ecfdf5,stroke:#059669,color:#0f172a;
    class E,K bad; class G lock; class M,L ok;
```

<details><summary>ASCII fallback</summary>

```
login
 ├─ no user ─► dummy verify ─► 401
 └─ user ─► locked? ─yes─► 429 (+Retry-After, skip password)
            └─no─► password ok?
                    ├─ no ─► attempts++ ─► >=5? ─yes─► lock 15m ─► 401
                    │                       └no──────────────────► 401
                    └─ yes ─► reset ─► last_login_at=now ─► 200 {access,refresh}
```

</details>

Unknown-email and wrong-password both return the same `401` and both pay a bcrypt
verify (a dummy hash when no user exists), so response timing can't reveal whether an
account exists (AC-AUTH-05 / FR-09).

## Wire the frontend to it

```bash
# frontend/.env
VITE_API_BASE=http://localhost:8000
```

Run both; the UI's invalid-credentials and lockout alerts are now driven by real
`401`/`429` responses. CORS is preconfigured for `http://localhost:5173`.

## Project layout

```
app/
  config.py     settings (DATABASE_URL, JWT, lockout, CORS)
  database.py   engine + session + Base + get_db
  models.py     User + UserStatus/UserRole enums
  schemas.py    Pydantic request/response + password-complexity validator
  passwords.py  pwdlib bcrypt hashing + dummy-hash timing equaliser
  tokens.py     PyJWT issue/verify (HS256, RS256-ready) + opaque refresh token
  deps.py       OAuth2 bearer scheme + get_current_user
  services.py   register_user + authenticate (lockout)
  routers/auth.py   /auth/register, /auth/login, /auth/me
  main.py       app + CORS
migrations/     Alembic (0001_create_users)
tests/          pytest: register/login/401/409/422/429 + protected route
```

## Out of scope (this iteration)

- **Refresh-token persistence/rotation**, `/auth/refresh`, `/auth/logout` — the BRD
  `refresh_tokens` table is modelled in the spec but not built; the refresh token is
  issued at login (to satisfy the response shape) but not yet stored or accepted.
- **Password reset & email verification** — the frontend's forgot-password call is
  enumeration-safe and ignores the response, so it degrades gracefully without the
  endpoint.
- Real email sending, breached-password (HIBP) check, RS256 keypair.

## Deviations from the BRD (intentional, for this dev iteration)

- **Registration creates an `ACTIVE` account** (not `PENDING_VERIFICATION`) so
  register→login works without an email provider. The response returns the real
  status. Flip the default in `services.register_user` once email exists.
- **Lockout window** is simplified: `failed_attempts` resets on success or after the
  lock expires, rather than tracking a precise 10-minute rolling window (the data
  model carries only `failed_attempts` + `locked_until`).
