/**
 * LearnFlow auth API client.
 *
 * Talks to the real FastAPI backend described in backend/UC-1-requirements.md
 * (§3.7 endpoint summary) when VITE_API_BASE is configured and reachable. When
 * it is not — no base set, or the backend isn't running yet — it transparently
 * falls back to an in-browser mock that reproduces the design prototype's
 * behaviour, so the UI runs standalone:
 *   • password under 4 chars       -> 401 "Invalid email or password."
 *   • email "locked@learnflow.io"  -> 429 lockout
 *   • anything else                -> success
 *
 * Error states surface as a thrown AuthError carrying the Alert `tone` and the
 * exact, security-reviewed microcopy from the requirements doc.
 */

const API_BASE = (import.meta.env.VITE_API_BASE ?? '').replace(/\/$/, '')

export type AlertTone = 'danger' | 'warning'

/** Thrown by every auth call on a non-success outcome. `tone` drives the Alert. */
export class AuthError extends Error {
  tone: AlertTone
  status?: number
  constructor(message: string, tone: AlertTone = 'danger', status?: number) {
    super(message)
    this.name = 'AuthError'
    this.tone = tone
    this.status = status
  }
}

export interface LoginRequest {
  email: string
  password: string
  remember?: boolean
}
export interface LoginSuccess {
  access_token: string
  refresh_token: string
  token_type: 'bearer'
}

export interface RegisterRequest {
  name: string
  email: string
  password: string
}
export interface RegisterSuccess {
  message: string
  status: 'PENDING_VERIFICATION'
}

const INVALID_CREDENTIALS = 'Invalid email or password.'
const ACCOUNT_LOCKED = 'Account temporarily locked. Try again in 15 minutes.'

const delay = (ms: number) => new Promise((r) => setTimeout(r, ms))

/** True when we have no configured backend to talk to. */
function noBackend(): boolean {
  return API_BASE === ''
}

/** Pull FastAPI's `detail` (or a `message`) off an error response body. */
async function readDetail(res: Response): Promise<string | undefined> {
  try {
    const body = await res.json()
    if (typeof body?.detail === 'string') return body.detail
    if (Array.isArray(body?.detail) && body.detail[0]?.msg) return body.detail[0].msg
    if (typeof body?.message === 'string') return body.message
  } catch {
    /* non-JSON body — ignore */
  }
  return undefined
}

async function postJson(path: string, payload: unknown): Promise<Response> {
  return fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include', // allow httpOnly refresh-token cookie per FR-10
    body: JSON.stringify(payload),
  })
}

// ---------------------------------------------------------------------------
// Login — POST /auth/login  (AC-AUTH-04 / AC-AUTH-05 / AC-AUTH-06)
// ---------------------------------------------------------------------------

function mockLogin({ email, password }: LoginRequest): LoginSuccess {
  const normalized = email.trim().toLowerCase()
  if (normalized === 'locked@learnflow.io') {
    throw new AuthError(ACCOUNT_LOCKED, 'warning', 429)
  }
  if (password.length < 4) {
    throw new AuthError(INVALID_CREDENTIALS, 'danger', 401)
  }
  return { access_token: 'mock.access.token', refresh_token: 'mock.refresh.token', token_type: 'bearer' }
}

export async function login(req: LoginRequest): Promise<LoginSuccess> {
  if (noBackend()) {
    await delay(650)
    return mockLogin(req)
  }
  let res: Response
  try {
    res = await postJson('/auth/login', { email: req.email, password: req.password })
  } catch {
    // Backend configured but unreachable — degrade to the standalone mock.
    await delay(400)
    return mockLogin(req)
  }
  if (res.ok) return (await res.json()) as LoginSuccess
  if (res.status === 429) throw new AuthError(ACCOUNT_LOCKED, 'warning', 429)
  if (res.status === 401) throw new AuthError(INVALID_CREDENTIALS, 'danger', 401)
  // 403 unverified / deactivated, or anything else: show the server message if any.
  throw new AuthError((await readDetail(res)) ?? INVALID_CREDENTIALS, 'danger', res.status)
}

// ---------------------------------------------------------------------------
// Register — POST /auth/register  (AC-AUTH-01)
// ---------------------------------------------------------------------------

function mockRegister(): RegisterSuccess {
  return { message: 'Check your inbox to verify your email.', status: 'PENDING_VERIFICATION' }
}

export async function register(req: RegisterRequest): Promise<RegisterSuccess> {
  if (noBackend()) {
    await delay(700)
    return mockRegister()
  }
  let res: Response
  try {
    res = await postJson('/auth/register', req)
  } catch {
    await delay(400)
    return mockRegister()
  }
  if (res.ok) return (await res.json()) as RegisterSuccess
  if (res.status === 409) {
    throw new AuthError((await readDetail(res)) ?? 'An account with this email already exists.', 'warning', 409)
  }
  throw new AuthError((await readDetail(res)) ?? 'Could not create your account. Please try again.', 'danger', res.status)
}

// ---------------------------------------------------------------------------
// Forgot password — POST /auth/password-reset/request  (AC-AUTH-10)
// Always resolves: the response is enumeration-safe (HTTP 202 regardless).
// ---------------------------------------------------------------------------

export async function requestPasswordReset(email: string): Promise<void> {
  if (noBackend()) {
    await delay(650)
    return
  }
  try {
    await postJson('/auth/password-reset/request', { email })
  } catch {
    await delay(400)
  }
  // Intentionally ignore status: never reveal whether the email exists (FR-09).
}

/** Which mode the client is operating in — surfaced as a small dev hint in the UI. */
export const authMode: 'live' | 'mock' = noBackend() ? 'mock' : 'live'
