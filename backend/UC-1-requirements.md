# LearnFlow LMS — Authentication Feature

**Document type:** Business Requirements Document (excerpt)
**Feature area:** User Identity & Access — Registration, Login, JWT, Password Reset
**Stack context:** FastAPI · React 19 · PostgreSQL 17 · JWT (Bearer tokens)
**Status:** Draft v0.2
**Author:** Business Analysis — LearnFlow Team

---

## 1. User Stories

### 1.1 Registration

**US-AUTH-01 — New learner self-registration**
> As a **prospective learner**,
> I want to **create an account using my email address and a password**,
> so that **I can access LearnFlow courses and track my learning progress**.

**US-AUTH-02 — Duplicate account prevention**
> As a **prospective learner who already has an account**,
> I want to **be clearly told that my email is already registered**,
> so that **I am not confused by a silent failure and can proceed to log in instead**.

**US-AUTH-03 — Email verification**
> As a **newly registered learner**,
> I want to **verify my email address before my account is activated**,
> so that **LearnFlow can confirm my identity and protect the platform from fake accounts**.

### 1.2 Login

**US-AUTH-04 — Standard email/password login**
> As a **registered learner**,
> I want to **log in with my email and password**,
> so that **I can access my personalised dashboard and enrolled courses**.

**US-AUTH-05 — Login failure feedback**
> As a **learner who enters wrong credentials**,
> I want to **receive a clear, non-specific error message**,
> so that **I know the attempt failed without exposing which field was incorrect** (security).

**US-AUTH-06 — Brute-force protection**
> As the **LearnFlow platform**,
> I want to **temporarily lock an account after repeated failed login attempts**,
> so that **automated credential-stuffing attacks are blocked**.

### 1.3 JWT Issuing & Session Management

**US-AUTH-07 — JWT access token on login**
> As a **successfully authenticated learner**,
> I want to **receive a short-lived JWT access token**,
> so that **subsequent API calls are authorised without re-entering my credentials**.

**US-AUTH-08 — Refresh token rotation**
> As an **active learner mid-session**,
> I want **my access token to be silently refreshed using a refresh token**,
> so that **my session continues seamlessly without repeated login prompts**.

**US-AUTH-09 — Logout & token invalidation**
> As a **learner who has finished a session**,
> I want to **log out and have my tokens invalidated server-side**,
> so that **my account cannot be accessed from a stolen or shared device**.

### 1.4 Password Reset

**US-AUTH-10 — Self-service password reset request**
> As a **learner who has forgotten their password**,
> I want to **request a password reset link via my registered email**,
> so that **I can regain access to my account without contacting support**.

**US-AUTH-11 — Secure one-time reset link**
> As a **learner who has received a reset link**,
> I want to **use it once within a time-limited window to set a new password**,
> so that **the link cannot be replayed or exploited if intercepted**.

**US-AUTH-12 — Post-reset session clean-up**
> As a **learner who has just reset their password**,
> I want **all existing active sessions to be invalidated**,
> so that **any unauthorised actor who had access is immediately locked out**.

---

## 2. Acceptance Criteria

### 2.1 Registration

**AC-AUTH-01 — Successful registration**

```
Given  a prospective learner is on the registration page
  And  provides a valid, previously unused email address
  And  provides a password meeting complexity rules (≥ 8 chars, 1 uppercase, 1 digit, 1 special char)
When   they submit the registration form
Then   the system creates a new user record in PostgreSQL with status = PENDING_VERIFICATION
  And  sends a verification email to the supplied address containing a signed, time-limited token (TTL: 24 h)
  And  returns HTTP 201 with a non-sensitive confirmation message
  And  does NOT issue a JWT access token yet
```

**AC-AUTH-02 — Duplicate email rejection**

```
Given  a prospective learner submits a registration form
  And  the email address already exists in the users table
When   FastAPI processes the request
Then   the system returns HTTP 409 Conflict
  And  the response body contains the message "An account with this email already exists."
  And  no duplicate user record is created
```

**AC-AUTH-03 — Email verification activation**

```
Given  a learner clicks the verification link from the confirmation email
  And  the token is valid and has not expired
When   the verification endpoint processes the token
Then   the user record status changes from PENDING_VERIFICATION to ACTIVE
  And  the token is marked as consumed (single-use)
  And  the learner is redirected to the login page with a success banner
```

**AC-AUTH-03b — Expired or invalid verification token**

```
Given  a learner clicks a verification link
  And  the token is expired or malformed
When   the verification endpoint processes the token
Then   HTTP 400 is returned
  And  the learner is offered a "Resend verification email" action
```

### 2.2 Login

**AC-AUTH-04 — Successful login**

```
Given  a learner with an ACTIVE account submits correct credentials
When   the FastAPI /auth/login endpoint processes the request
Then   HTTP 200 is returned
  And  the response body contains:
         - access_token  (JWT, signed HS256/RS256, TTL: 15 min)
         - refresh_token (opaque, stored server-side, TTL: 7 days)
         - token_type: "bearer"
  And  the failed_login_attempts counter is reset to 0
  And  last_login_at is updated in PostgreSQL
```

**AC-AUTH-05 — Invalid credentials**

```
Given  a learner submits an unrecognised email OR an incorrect password
When   the FastAPI /auth/login endpoint processes the request
Then   HTTP 401 is returned
  And  the response body contains only "Invalid email or password." (no field-level distinction)
  And  failed_login_attempts is incremented
  And  response time is normalised (constant-time comparison) to prevent timing attacks
```

**AC-AUTH-06 — Account lockout**

```
Given  a learner account has accumulated 5 failed login attempts within 10 minutes
When   a further login attempt is made (valid or invalid credentials)
Then   HTTP 429 is returned with message "Account temporarily locked. Try again in 15 minutes."
  And  an alert email is dispatched to the account's registered address
  And  a LearnFlow admin can manually unlock the account via the admin panel
```

### 2.3 JWT Issuing & Session Management

**AC-AUTH-07 — JWT structure and claims**

```
Given  a successful login has occurred
When   the access token is decoded (after signature verification)
Then   the JWT payload contains:
         - sub       : user UUID (not email, not integer PK)
         - role      : e.g. "learner" | "instructor" | "admin"
         - iat       : issued-at timestamp
         - exp       : expiry (iat + 900 s)
         - jti       : unique token ID (for revocation tracking)
  And  the JWT is signed with the server's private key (RS256 recommended)
  And  the JWT is NOT stored in localStorage on the React client (use httpOnly cookie or memory)
```

**AC-AUTH-08 — Access token refresh**

```
Given  a learner's access token has expired
  And  they hold a valid, non-revoked refresh token
When   the React client calls POST /auth/refresh
Then   HTTP 200 is returned with a new access_token (TTL reset to 15 min)
  And  the old refresh token is invalidated (rotation)
  And  a new refresh token is issued
```

**AC-AUTH-08b — Refresh token reuse detection**

```
Given  a refresh token has already been rotated (used once)
When   the same refresh token is submitted again
Then   HTTP 401 is returned
  And  ALL active sessions for that user are invalidated (compromise assumed)
  And  the user is notified by email of a potential account compromise
```

**AC-AUTH-09 — Logout**

```
Given  a learner is authenticated and calls POST /auth/logout
When   FastAPI processes the request
Then   the current refresh token is added to the server-side revocation store
  And  HTTP 204 No Content is returned
  And  the React client clears the access token from memory
  And  subsequent requests using the old access token return HTTP 401 after its TTL expires
```

### 2.4 Password Reset

**AC-AUTH-10 — Reset request**

```
Given  a learner submits POST /auth/password-reset/request with a registered email
When   FastAPI processes the request
Then   HTTP 202 Accepted is returned regardless of whether the email exists (prevents enumeration)
  And  IF the email exists, a password-reset email is sent containing a signed URL with a token (TTL: 1 h)
  And  the token is stored (hashed) in the password_reset_tokens table linked to the user
```

**AC-AUTH-11 — Completing the reset**

```
Given  a learner submits a new password via POST /auth/password-reset/confirm
  And  the reset token in the request is valid, unexpired, and not previously used
When   FastAPI processes the request
Then   the user's password hash is updated in PostgreSQL
  And  the reset token is marked as consumed
  And  HTTP 200 is returned with message "Password updated. Please log in."
  And  the learner is NOT automatically logged in
```

**AC-AUTH-11b — Invalid/expired reset token**

```
Given  a learner submits a reset token that is expired or already consumed
When   FastAPI processes the request
Then   HTTP 400 is returned with message "This link is invalid or has expired."
  And  the learner is offered a link to request a new reset email
```

**AC-AUTH-12 — Session invalidation after reset**

```
Given  a password reset has been successfully completed
When   FastAPI finalises the reset
Then   all refresh tokens associated with that user are invalidated in the revocation store
  And  the user's token_version (or equivalent) is incremented, invalidating all existing JWTs
  And  an email confirming the password change is sent to the registered address
```

---

## 3. Business Requirements Document — Authentication Module

### 3.1 Purpose

This section defines the business requirements for the **User Authentication** capability of LearnFlow LMS. Authentication is the foundation of personalised learning: every feature — course enrolment, progress tracking, certification, and instructor management — depends on a verified, persistent user identity.

### 3.2 Business Objectives

| #    | Objective                                                          | Metric                                                          |
| ---- | ------------------------------------------------------------------ | --------------------------------------------------------------- |
| BO-1 | Reduce friction at account creation to increase learner activation | Registration-to-first-course-start rate ≥ 70 % within 48 h      |
| BO-2 | Protect learner data and platform integrity                        | Zero credential-breach incidents attributable to auth layer     |
| BO-3 | Minimise support burden for access issues                          | Password-reset self-service rate ≥ 95 % (support tickets < 5 %) |
| BO-4 | Meet compliance obligations (DPDPA 2023, GDPR-aligned)             | Annual audit pass; no reportable data incidents                 |

### 3.3 Scope

**In scope:**

- Learner self-registration (email + password)
- Email verification flow
- Email/password login
- JWT access token and refresh token issuance and rotation
- Logout with server-side token revocation
- Self-service password reset via email link
- Account lockout after repeated failures
- React 19 frontend integration (auth state management, protected routes)
- FastAPI backend endpoints (`/auth/*`)
- PostgreSQL 17 schema additions (`users`, `refresh_tokens`, `password_reset_tokens`)

**Out of scope (future phases):**

- Social / OAuth login (Google, LinkedIn)
- Multi-factor authentication (MFA / TOTP)
- Single Sign-On (SSO / SAML) for enterprise clients
- Instructor and admin account provisioning workflows

### 3.4 Functional Requirements

| ID    | Requirement                                                                                 | Priority  |
| ----- | ------------------------------------------------------------------------------------------- | --------- |
| FR-01 | The system shall allow any visitor to register with a unique email and a compliant password | Must Have |
| FR-02 | The system shall verify registrant email addresses before activating accounts               | Must Have |
| FR-03 | The system shall authenticate users via email/password and issue a signed JWT               | Must Have |
| FR-04 | The system shall issue a rotating refresh token alongside the access token                  | Must Have |
| FR-05 | The system shall lock accounts after 5 failed login attempts within 10 minutes              | Must Have |
| FR-06 | The system shall allow authenticated users to log out and revoke their tokens               | Must Have |
| FR-07 | The system shall provide a self-service password reset flow via email                       | Must Have |
| FR-08 | Password reset shall invalidate all existing sessions for that user                         | Must Have |
| FR-09 | All API responses shall avoid leaking existence of accounts to unauthenticated requests     | Must Have |
| FR-10 | The frontend shall store tokens in memory or httpOnly cookies — never localStorage          | Must Have |

### 3.5 Non-Functional Requirements

| ID     | Requirement                                  | Target                                                                              |
| ------ | -------------------------------------------- | ----------------------------------------------------------------------------------- |
| NFR-01 | **Performance** — Login endpoint p95 latency | ≤ 300 ms under 500 concurrent users                                                 |
| NFR-02 | **Security** — Password hashing algorithm    | bcrypt with cost factor ≥ 12, or Argon2id                                           |
| NFR-03 | **Security** — JWT signing algorithm         | RS256 (asymmetric); HS256 only if key management justifies it                       |
| NFR-04 | **Availability** — Auth service uptime       | 99.9 % monthly                                                                      |
| NFR-05 | **Compliance** — PII handling                | Passwords never stored in plain text or logs; emails pseudonymised in logs          |
| NFR-06 | **Observability** — Auth events logged       | Login success/failure, lockout, reset, logout — all auditable with timestamp and IP |

### 3.6 Data Model (Summary)

```
users
  id                UUID PK
  email             VARCHAR(255) UNIQUE NOT NULL
  password_hash     VARCHAR NOT NULL
  status            ENUM(PENDING_VERIFICATION, ACTIVE, LOCKED, DEACTIVATED)
  role              ENUM(learner, instructor, admin)
  failed_attempts   SMALLINT DEFAULT 0
  locked_until      TIMESTAMPTZ NULL
  token_version     INTEGER DEFAULT 0   -- increment to bulk-invalidate JWTs
  last_login_at     TIMESTAMPTZ NULL
  created_at        TIMESTAMPTZ DEFAULT now()

refresh_tokens
  id                UUID PK
  user_id           UUID FK → users.id
  token_hash        VARCHAR NOT NULL    -- store hash, not raw token
  issued_at         TIMESTAMPTZ
  expires_at        TIMESTAMPTZ
  revoked_at        TIMESTAMPTZ NULL
  replaced_by       UUID NULL           -- for rotation chain

password_reset_tokens
  id                UUID PK
  user_id           UUID FK → users.id
  token_hash        VARCHAR NOT NULL
  expires_at        TIMESTAMPTZ
  consumed_at       TIMESTAMPTZ NULL

email_verification_tokens
  id                UUID PK
  user_id           UUID FK → users.id
  token_hash        VARCHAR NOT NULL
  expires_at        TIMESTAMPTZ
  consumed_at       TIMESTAMPTZ NULL
```

### 3.7 API Endpoint Summary

| Method | Path                           | Description                                |
| ------ | ------------------------------ | ------------------------------------------ |
| `POST` | `/auth/register`               | Create new user account                    |
| `GET`  | `/auth/verify-email?token=`    | Activate account via email link            |
| `POST` | `/auth/login`                  | Authenticate and receive JWT pair          |
| `POST` | `/auth/refresh`                | Rotate refresh token, get new access token |
| `POST` | `/auth/logout`                 | Revoke current refresh token               |
| `POST` | `/auth/password-reset/request` | Trigger reset email                        |
| `POST` | `/auth/password-reset/confirm` | Set new password via token                 |

### 3.8 Dependencies & Assumptions

- **Email service:** A transactional email provider (e.g. AWS SES, SendGrid) must be configured before registration and password-reset flows can go live.
- **Secret management:** JWT signing keys and email credentials are stored in environment variables / Vault — not in source code.
- **Frontend routing:** React 19 router will implement protected routes that redirect unauthenticated users to `/login`.
- **HTTPS:** All auth endpoints are served exclusively over TLS in staging and production.
- **Assumption:** Username-based identity is out of scope; email is the sole identifier in this phase.

### 3.9 Risks

| Risk                                              | Likelihood | Impact   | Mitigation                                                                        |
| ------------------------------------------------- | ---------- | -------- | --------------------------------------------------------------------------------- |
| Email deliverability issues block verification    | Medium     | High     | Monitor bounce rates; offer "resend" CTA; consider SMS fallback (Phase 2)         |
| Refresh token database becomes a hotspot at scale | Low        | Medium   | Index on `user_id` + `expires_at`; consider Redis for revocation store            |
| JWT signing key compromise                        | Low        | Critical | Rotate keys via versioned secrets; token_version allows immediate bulk revocation |
| Regulation change (DPDPA enforcement)             | Medium     | Medium   | Keep PII handling reviewed quarterly; DPA contact designated                      |

---

## 4. Edge-Case Acceptance Criteria

> **Scope note.** This section enumerates every meaningful deviation from the happy path across all four auth flows. Each AC is self-contained and cross-referenced to the relevant functional requirement. IDs use the prefix **EC-AUTH-** to distinguish them from the happy-path ACs in §2.
>
> **Enumeration approach.** Edge cases are classified by the axis of failure:
>
> - **Input validity** — malformed or policy-violating inputs supplied by the client
> - **State conflicts** — the database / system state contradicts the request
> - **Token lifecycle** — tokens that are expired, consumed, replayed, or structurally invalid
> - **Security probes** — inputs designed to extract information or escalate privilege
> - **Infrastructure / timing** — transient failures that must degrade gracefully

### 4.1 Registration Edge Cases

**EC-AUTH-REG-01 — Duplicate email (ACTIVE account)**
*Axis: State conflict | Ref: FR-01, AC-AUTH-02*

```
Given  a POST /auth/register request is received
  And  the submitted email already exists in the users table
  And  the matching account has status = ACTIVE
When   FastAPI processes the request
Then   HTTP 409 Conflict is returned
  And  the response body contains: "An account with this email already exists."
  And  the response body includes a link/hint to the login page
  And  NO new user row is inserted
  And  NO verification email is sent
  And  the existing account's password hash is NOT modified
  And  the event is logged with severity INFO (not an attack signal at this point)
```

**EC-AUTH-REG-02 — Duplicate email (PENDING_VERIFICATION account)**
*Axis: State conflict | Ref: FR-01, FR-02*

```
Given  a POST /auth/register request is received
  And  the submitted email already exists with status = PENDING_VERIFICATION
  And  the original verification token has NOT yet expired
When   FastAPI processes the request
Then   HTTP 409 Conflict is returned
  And  the response body contains:
       "This email is already registered but not yet verified.
        Check your inbox or request a new verification link."
  And  a "Resend verification email" link is included in the response
  And  NO second user row is inserted
  And  a new verification token is NOT automatically issued
       (rate-limit: resend only on explicit learner action)
```

**EC-AUTH-REG-03 — Duplicate email (PENDING_VERIFICATION, original token expired)**
*Axis: State conflict + Token lifecycle | Ref: FR-01, FR-02*

```
Given  a POST /auth/register request is received
  And  the email exists with status = PENDING_VERIFICATION
  And  the original verification token IS expired
When   FastAPI processes the request
Then   HTTP 409 Conflict is returned with the same "not yet verified" message
  And  a new verification token is generated and the expiry reset (TTL: 24 h)
  And  a fresh verification email is dispatched to the address
  And  the old expired token is marked consumed/superseded in the DB
  And  the user row created_at is NOT changed (preserves original registration audit trail)
```

**EC-AUTH-REG-04 — Weak password — too short**
*Axis: Input validity | Ref: FR-01, NFR-02*

```
Given  a POST /auth/register request is received
  And  the password field contains fewer than 8 characters (e.g. "Abc1!")
When   FastAPI's Pydantic validation runs
Then   HTTP 422 Unprocessable Entity is returned before any DB write
  And  the error detail array contains:
       { field: "password", msg: "Password must be at least 8 characters." }
  And  no user record is created
  And  no verification email is sent
```

**EC-AUTH-REG-05 — Weak password — missing required character classes**
*Axis: Input validity | Ref: FR-01, NFR-02*

```
Given  a POST /auth/register request is received
  And  the password is ≥ 8 characters but violates one or more rules:
       - no uppercase letter, OR
       - no digit, OR
       - no special character (!@#$%^&* etc.)
When   FastAPI's Pydantic validation runs
Then   HTTP 422 is returned with a field-level error for each violated rule
  And  ALL failing rules are reported in a single response
       (not revealed one-at-a-time, to avoid iterative probing)
  And  the error messages name the rule class but NOT the missing character
       e.g. "Password must contain at least one digit."
  And  no user record is created
```

**EC-AUTH-REG-06 — Weak password — breached / commonly used password**
*Axis: Input validity + Security probe | Ref: FR-01, NFR-02*

```
Given  a POST /auth/register request is received
  And  the password meets all local complexity rules
  And  the password appears in the application's blocked-password list
       (derived from HaveIBeenPwned corpus or equivalent, checked via k-anonymity API)
When   FastAPI processes the request
Then   HTTP 422 is returned
  And  the error message is:
       "This password is too commonly used. Please choose a different one."
  And  the specific matched entry is NOT disclosed
  And  no user record is created
```

**EC-AUTH-REG-07 — Malformed email format**
*Axis: Input validity | Ref: FR-01*

```
Given  a POST /auth/register request is received
  And  the email field fails RFC 5322 format validation
       (e.g. "notanemail", "user@", "@domain.com", "user @domain.com")
When   FastAPI's Pydantic EmailStr validation runs
Then   HTTP 422 is returned with:
       { field: "email", msg: "Enter a valid email address." }
  And  no DB write occurs
  And  no email is dispatched
```

**EC-AUTH-REG-08 — Password and email identical (credential stuffing risk)**
*Axis: Security probe | Ref: FR-01, NFR-02*

```
Given  a POST /auth/register request is received
  And  the password value equals the email address (case-insensitive)
When   FastAPI validates the registration payload
Then   HTTP 422 is returned
  And  the error message is:
       "Your password cannot be the same as your email address."
  And  no user record is created
```

**EC-AUTH-REG-09 — Email verification token already consumed**
*Axis: Token lifecycle | Ref: FR-02*

```
Given  a learner clicks a verification link
  And  the token exists in email_verification_tokens
  And  consumed_at is NOT NULL (token was already used successfully)
When   GET /auth/verify-email?token=<token> is processed
Then   HTTP 400 is returned
  And  the response message is:
       "This verification link has already been used. If your account is active, please log in."
  And  the user's status is NOT changed a second time
  And  no new token is issued automatically
```

### 4.2 Login Edge Cases

**EC-AUTH-LGN-01 — Login attempt on PENDING_VERIFICATION account**
*Axis: State conflict | Ref: FR-03*

```
Given  a POST /auth/login request is received with correct credentials
  And  the matching user record has status = PENDING_VERIFICATION
When   FastAPI processes the authentication
Then   HTTP 403 Forbidden is returned
  And  the response body is:
       "Your email address has not been verified.
        Please check your inbox or request a new verification link."
  And  NO JWT or refresh token is issued
  And  failed_login_attempts is NOT incremented
       (correct credentials + unverified = expected state, not an attack signal)
  And  a "Resend verification email" action is surfaced
```

**EC-AUTH-LGN-02 — Login attempt on LOCKED account (auto-lock)**
*Axis: State conflict | Ref: FR-05, AC-AUTH-06*

```
Given  a POST /auth/login request is received
  And  the matching user has status = LOCKED or failed_attempts ≥ 5 within the window
  And  locked_until is in the future
When   FastAPI processes the request (credential check is skipped)
Then   HTTP 429 Too Many Requests is returned
  And  the Retry-After header is set to the seconds remaining until locked_until
  And  the response body is:
       "Account temporarily locked due to repeated failed attempts.
        Try again in X minutes." (X computed from locked_until)
  And  the submitted password is NOT evaluated (prevents timing oracle)
  And  the failed_attempts counter is NOT further incremented
```

**EC-AUTH-LGN-03 — Login attempt on DEACTIVATED account**
*Axis: State conflict | Ref: FR-03*

```
Given  a POST /auth/login request is received
  And  the matching user record has status = DEACTIVATED
When   FastAPI processes the request
Then   HTTP 403 Forbidden is returned
  And  the response body is:
       "This account has been deactivated. Please contact support."
  And  NO JWT or refresh token is issued
  And  the response is returned in constant time
       (same duration as a failed password check, to prevent account existence enumeration)
```

**EC-AUTH-LGN-04 — Login with correct email, wrong password — lockout threshold approach**
*Axis: Security probe | Ref: FR-05*

```
Given  a POST /auth/login request is received with a known email but wrong password
  And  failed_attempts is currently 4 (one attempt away from lockout)
When   FastAPI processes the failed authentication
Then   HTTP 401 is returned with the standard "Invalid email or password." message
  And  failed_attempts is incremented to 5
  And  the account is immediately locked (locked_until = now() + 15 min)
  And  an alert email is dispatched to the registered address
  And  the response does NOT mention the imminent or actual lockout
       (prevents attacker from knowing they hit the threshold)
```

**EC-AUTH-LGN-05 — Login for a non-existent email**
*Axis: Security probe (account enumeration) | Ref: FR-09*

```
Given  a POST /auth/login request is received
  And  the submitted email does NOT exist in the users table
When   FastAPI processes the request
Then   HTTP 401 is returned
  And  the response body is identical to a wrong-password response:
       "Invalid email or password."
  And  the response time is normalised to match the bcrypt/Argon2 comparison duration
       (dummy hash comparison performed even when no user row found)
  And  no information about the email's absence is revealed
```

### 4.3 JWT / Token Lifecycle Edge Cases

**EC-AUTH-JWT-01 — Expired access token presented to a protected endpoint**
*Axis: Token lifecycle | Ref: FR-03, FR-04*

```
Given  a learner presents a Bearer token to any protected endpoint
  And  the token's exp claim is in the past
When   FastAPI's JWT middleware validates the token
Then   HTTP 401 Unauthorized is returned
  And  the WWW-Authenticate header is set to:
       Bearer realm="learnflow", error="token_expired"
  And  the response body is: "Access token has expired. Please refresh your session."
  And  the React client intercepts the 401 and automatically calls POST /auth/refresh
       before retrying the original request (silent refresh pattern)
```

**EC-AUTH-JWT-02 — Tampered / invalid JWT signature**
*Axis: Security probe | Ref: FR-03*

```
Given  a learner presents a Bearer token
  And  the token's signature does not match the server's public key
       (e.g. alg:none attack, key confusion, manual payload modification)
When   FastAPI's JWT middleware validates the token
Then   HTTP 401 is returned immediately
  And  WWW-Authenticate header: Bearer realm="learnflow", error="invalid_token"
  And  the event is logged at severity WARNING with the source IP and raw token header
  And  no claims from the token payload are trusted or acted upon
  And  the algorithm field is validated against the server's ALLOWED_ALGORITHMS allowlist
       (rejects "none", rejects unexpected algorithms)
```

**EC-AUTH-JWT-03 — JWT token_version mismatch (stale token after password reset)**
*Axis: Token lifecycle | Ref: FR-08, AC-AUTH-12*

```
Given  a learner completes a password reset (token_version incremented to N+1)
  And  a previously issued JWT still contains token_version = N
When   that old JWT is presented to any protected endpoint
Then   HTTP 401 is returned
  And  the response body is: "Your session has been invalidated. Please log in again."
  And  the React client clears stored tokens and redirects to /login
  And  no resource data is returned
```

**EC-AUTH-JWT-04 — Refresh token presented after explicit logout**
*Axis: Token lifecycle | Ref: FR-06, AC-AUTH-09*

```
Given  a learner has called POST /auth/logout
  And  their refresh token has been added to the server-side revocation store
When   the same refresh token is submitted to POST /auth/refresh
Then   HTTP 401 is returned
  And  the response body is: "Session has ended. Please log in again."
  And  NO new access token or refresh token is issued
  And  the revocation store entry is NOT removed (idempotent — prevents replay window)
```

**EC-AUTH-JWT-05 — Refresh token presented after its expiry**
*Axis: Token lifecycle | Ref: FR-04*

```
Given  a learner submits a refresh token to POST /auth/refresh
  And  the token's expires_at timestamp is in the past
  And  the token has NOT been explicitly revoked
When   FastAPI processes the refresh request
Then   HTTP 401 is returned
  And  the response body is:
       "Your session has expired. Please log in again."
  And  the expired token row is marked revoked_at = now() (housekeeping)
  And  NO new token pair is issued
  And  the React client redirects the learner to /login
```

**EC-AUTH-JWT-06 — Refresh token reuse (rotation violation / token theft signal)**
*Axis: Security probe | Ref: FR-04, AC-AUTH-08b*

```
Given  refresh token RT-A was previously rotated and replaced by RT-B
  And  RT-A has replaced_by = RT-B's ID in the refresh_tokens table
When   RT-A is submitted again to POST /auth/refresh
Then   HTTP 401 is returned
  And  ALL active refresh tokens for that user are immediately revoked
       (the entire token family is invalidated)
  And  the user's token_version is incremented (invalidates all outstanding JWTs)
  And  a security-alert email is dispatched:
       "Unusual activity detected on your LearnFlow account.
        All sessions have been signed out as a precaution."
  And  the event is logged at severity CRITICAL with IP, user ID, and token IDs
```

### 4.4 Password Reset Edge Cases

**EC-AUTH-PWR-01 — Reset request for a non-existent email**
*Axis: Security probe (account enumeration) | Ref: FR-07, FR-09, AC-AUTH-10*

```
Given  a POST /auth/password-reset/request is received
  And  the submitted email does NOT exist in the users table
When   FastAPI processes the request
Then   HTTP 202 Accepted is returned (identical to the success response)
  And  the response body is:
       "If an account exists for this email, a reset link has been sent."
  And  NO email is dispatched
  And  NO token row is created in password_reset_tokens
  And  the response time is normalised to match the time taken when the email DOES exist
       (prevents timing-based enumeration)
  And  the event is logged at INFO with the submitted address redacted/hashed
```

**EC-AUTH-PWR-02 — Reset request for a PENDING_VERIFICATION account**
*Axis: State conflict | Ref: FR-07*

```
Given  a POST /auth/password-reset/request is received
  And  the email exists with status = PENDING_VERIFICATION
When   FastAPI processes the request
Then   HTTP 202 Accepted is returned (enumeration-safe surface)
  And  instead of a reset link, the email dispatched contains:
       "Your account is not yet verified. Please verify your email first."
       with a fresh verification link (TTL: 24 h)
  And  NO password_reset_tokens row is created
  And  the existing password hash is NOT modified
```

**EC-AUTH-PWR-03 — Reset request for a LOCKED account**
*Axis: State conflict | Ref: FR-07*

```
Given  a POST /auth/password-reset/request is received
  And  the email exists with status = LOCKED (auto-locked due to failed attempts)
When   FastAPI processes the request
Then   HTTP 202 Accepted is returned (enumeration-safe)
  And  a reset email IS dispatched — password reset is the legitimate recovery path
  And  upon successful password reset (EC-AUTH-PWR-05 below):
       - failed_attempts is reset to 0
       - locked_until is cleared
       - status is restored to ACTIVE
```

**EC-AUTH-PWR-04 — Reset request for a DEACTIVATED account**
*Axis: State conflict | Ref: FR-07*

```
Given  a POST /auth/password-reset/request is received
  And  the email exists with status = DEACTIVATED
When   FastAPI processes the request
Then   HTTP 202 Accepted is returned
  And  NO reset email is dispatched
  And  NO token is created
  And  the event is logged (admin visibility)
  And  behaviour is externally indistinguishable from the non-existent email case
       (EC-AUTH-PWR-01)
```

**EC-AUTH-PWR-05 — Expired password-reset token**
*Axis: Token lifecycle | Ref: FR-07, AC-AUTH-11b*

```
Given  a POST /auth/password-reset/confirm is received
  And  the reset token exists in password_reset_tokens
  And  expires_at < now() (token has expired)
  And  consumed_at IS NULL (token was never used)
When   FastAPI processes the request
Then   HTTP 400 Bad Request is returned
  And  the response body is:
       "This password reset link has expired. Please request a new one."
  And  the expired token is marked consumed_at = now() (prevent future replay attempts)
  And  the user's password hash is NOT modified
  And  a "Request new reset link" CTA is surfaced on the React error page
```

**EC-AUTH-PWR-06 — Already-consumed password-reset token (replay attempt)**
*Axis: Token lifecycle + Security probe | Ref: FR-07*

```
Given  a POST /auth/password-reset/confirm is received
  And  the token exists in password_reset_tokens
  And  consumed_at IS NOT NULL (token was already used successfully)
When   FastAPI processes the request
Then   HTTP 400 is returned
  And  the response body is:
       "This reset link has already been used. If you did not reset your password,
        contact support immediately."
  And  the user's password is NOT changed
  And  the event is logged at severity WARNING
       (second use could indicate token interception)
  And  a security-notification email is NOT automatically sent
       (risk of alert fatigue — log for admin review instead)
```

**EC-AUTH-PWR-07 — New password same as current password**
*Axis: Input validity | Ref: FR-07, NFR-02*

```
Given  a POST /auth/password-reset/confirm is received with a valid, unexpired token
  And  the submitted new_password, when hashed, matches the existing password_hash
When   FastAPI processes the request
Then   HTTP 422 is returned
  And  the response body is:
       "Your new password must be different from your current password."
  And  the password_reset_tokens row is NOT consumed
       (learner can retry with a genuinely new password using the same valid token)
  And  no session invalidation occurs
```

**EC-AUTH-PWR-08 — New password fails complexity rules**
*Axis: Input validity | Ref: FR-07, NFR-02*

```
Given  a POST /auth/password-reset/confirm is received with a valid, unexpired token
  And  the submitted new_password fails one or more complexity rules
       (same rules as EC-AUTH-REG-04 / EC-AUTH-REG-05)
When   FastAPI's Pydantic validation runs
Then   HTTP 422 is returned with field-level errors for each violated rule
  And  the reset token is NOT consumed (still valid for a corrected retry)
  And  the existing password hash is NOT modified
```

**EC-AUTH-PWR-09 — Multiple simultaneous outstanding reset tokens**
*Axis: State conflict | Ref: FR-07*

```
Given  a learner has requested a password reset (Token A, not yet consumed)
  And  the learner requests a second reset before Token A expires (Token B issued)
When   Token A is subsequently submitted to POST /auth/password-reset/confirm
Then   HTTP 400 is returned
  And  the response body is:
       "This link is no longer valid. A newer reset link has been sent to your inbox."
  And  Token A is consumed/superseded in the DB
  And  only Token B remains valid
  And  this behaviour is enforced by a latest_reset_token_id FK on the users table
       (or equivalent supersession flag)
```

### 4.5 Edge Case Summary Matrix

| ID             | Flow         | Axis             | HTTP Status | Enumeration-safe?                         | Token consumed?         |
| -------------- | ------------ | ---------------- | ----------- | ----------------------------------------- | ----------------------- |
| EC-AUTH-REG-01 | Registration | State conflict   | 409         | No (intentional — already logged in path) | —                       |
| EC-AUTH-REG-02 | Registration | State conflict   | 409         | No (intentional)                          | —                       |
| EC-AUTH-REG-03 | Registration | State + Token    | 409         | No                                        | Old token superseded    |
| EC-AUTH-REG-04 | Registration | Input validity   | 422         | —                                         | —                       |
| EC-AUTH-REG-05 | Registration | Input validity   | 422         | —                                         | —                       |
| EC-AUTH-REG-06 | Registration | Input + Security | 422         | —                                         | —                       |
| EC-AUTH-REG-07 | Registration | Input validity   | 422         | —                                         | —                       |
| EC-AUTH-REG-08 | Registration | Security probe   | 422         | —                                         | —                       |
| EC-AUTH-REG-09 | Registration | Token lifecycle  | 400         | —                                         | Not re-consumed         |
| EC-AUTH-LGN-01 | Login        | State conflict   | 403         | N/A                                       | —                       |
| EC-AUTH-LGN-02 | Login        | State conflict   | 429         | N/A                                       | —                       |
| EC-AUTH-LGN-03 | Login        | State conflict   | 403         | Yes (constant time)                       | —                       |
| EC-AUTH-LGN-04 | Login        | Security probe   | 401         | Yes                                       | —                       |
| EC-AUTH-LGN-05 | Login        | Security probe   | 401         | Yes (timing-normalised)                   | —                       |
| EC-AUTH-JWT-01 | JWT          | Token lifecycle  | 401         | —                                         | —                       |
| EC-AUTH-JWT-02 | JWT          | Security probe   | 401         | —                                         | —                       |
| EC-AUTH-JWT-03 | JWT          | Token lifecycle  | 401         | —                                         | —                       |
| EC-AUTH-JWT-04 | JWT          | Token lifecycle  | 401         | —                                         | Not re-revoked          |
| EC-AUTH-JWT-05 | JWT          | Token lifecycle  | 401         | —                                         | Marked revoked          |
| EC-AUTH-JWT-06 | JWT          | Security probe   | 401         | —                                         | Full family revoked     |
| EC-AUTH-PWR-01 | Pwd Reset    | Security probe   | 202         | Yes (timing-normalised)                   | —                       |
| EC-AUTH-PWR-02 | Pwd Reset    | State conflict   | 202         | Yes                                       | —                       |
| EC-AUTH-PWR-03 | Pwd Reset    | State conflict   | 202         | Yes                                       | —                       |
| EC-AUTH-PWR-04 | Pwd Reset    | State conflict   | 202         | Yes                                       | —                       |
| EC-AUTH-PWR-05 | Pwd Reset    | Token lifecycle  | 400         | —                                         | Consumed (housekeeping) |
| EC-AUTH-PWR-06 | Pwd Reset    | Token + Security | 400         | —                                         | Already consumed        |
| EC-AUTH-PWR-07 | Pwd Reset    | Input validity   | 422         | —                                         | NOT consumed (retry ok) |
| EC-AUTH-PWR-08 | Pwd Reset    | Input validity   | 422         | —                                         | NOT consumed (retry ok) |
| EC-AUTH-PWR-09 | Pwd Reset    | State conflict   | 400         | —                                         | Token A superseded      |

---

*Document updated: Edge Cases section (§4) appended — v0.2 Draft*
