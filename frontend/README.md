# LearnFlow Frontend — Auth (UC-1)

React 19 + Vite + TypeScript implementation of the **LearnFlow Auth** Claude Design
([source design](https://claude.ai/design/p/69d8c53f-bf71-4395-9a6e-ef66330c0a73)),
covering the login and registration flows of UC-1 (see `../backend/UC-1-requirements.md`).

## What's here

- Split-screen auth layout: indigo→teal brand panel + form column.
- **Login** — validation, demo credentials pre-filled, loading + success/error banners,
  "forgot password" (enumeration-safe reset request).
- **Register** — name/email/password/confirm with a live password-strength meter,
  terms acceptance, and a "check your inbox" verification screen on success.
- The LearnFlow Design System ported in:
  - tokens in `src/styles/tokens/` (colors, typography, spacing, fonts),
  - components in `src/components/` (`Logo`, `Alert`, `Button`, `Input`, `PasswordInput`, `Checkbox`).

## Auth client (real API + mock fallback)

`src/api/authClient.ts` POSTs to the FastAPI `/auth/*` endpoints when `VITE_API_BASE`
is set **and** the backend is reachable; otherwise it transparently falls back to an
in-browser mock so the UI runs standalone. Error semantics match the spec:

| Status | Meaning             | Message                                                  |
| ------ | ------------------- | -------------------------------------------------------- |
| 401    | invalid credentials | "Invalid email or password."                             |
| 403    | account not active  | unverified / deactivated                                 |
| 409    | duplicate email     | "An account with this email already exists."             |
| 429    | account locked      | "Account temporarily locked. Try again in 15 minutes."  |

**Mock demo account:** `learner@example.com` / `Password1!` (pre-filled on the login form).
Registering with that email returns a mock 409; five failed mock logins trigger a mock 429 lockout.

## Run

```bash
npm install
cp .env.example .env   # optionally set VITE_API_BASE=http://localhost:8000
npm run dev            # http://localhost:5173
```

Other scripts: `npm run build`, `npm run preview`, `npm run typecheck`.
