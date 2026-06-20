/**
 * LearnFlow auth client.
 *
 * When VITE_API_BASE is set AND the backend is reachable, requests go to the
 * FastAPI `/auth/*` endpoints described in the UC-1 requirements. If the base
 * is unset, or a network error occurs (backend down), the client transparently
 * falls back to an in-browser mock so the UI runs standalone.
 *
 * Error semantics are kept aligned with the spec:
 *   401  -> invalid credentials  ("Invalid email or password.")
 *   403  -> account not active    (unverified / deactivated)
 *   409  -> duplicate email       ("An account with this email already exists.")
 *   429  -> account locked        ("Account temporarily locked. Try again in 15 minutes.")
 */

const API_BASE = (import.meta.env.VITE_API_BASE ?? '').trim().replace(/\/$/, '');

/** Demo account recognised by the mock (matches the design's pre-filled creds). */
const DEMO_EMAIL = 'learner@example.com';
const DEMO_PASSWORD = 'Password1!';
const MOCK_LOCKOUT_THRESHOLD = 5;

export type AuthErrorCode =
  | 'invalid_credentials'
  | 'account_not_active'
  | 'duplicate_email'
  | 'account_locked'
  | 'validation'
  | 'unknown';

export class AuthError extends Error {
  code: AuthErrorCode;
  status?: number;

  constructor(code: AuthErrorCode, message: string, status?: number) {
    super(message);
    this.name = 'AuthError';
    this.code = code;
    this.status = status;
  }
}

export interface LoginResult {
  accessToken: string;
  tokenType: string;
  /** True when the result came from the in-browser mock rather than the API. */
  mocked: boolean;
}

export interface RegisterResult {
  message: string;
  mocked: boolean;
}

export interface ResetResult {
  message: string;
  mocked: boolean;
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function safeJson(res: Response): Promise<Record<string, unknown>> {
  try {
    return (await res.json()) as Record<string, unknown>;
  } catch {
    return {};
  }
}

/** Map an HTTP error response to a typed AuthError, preferring the server message. */
function errorForResponse(status: number, data: Record<string, unknown>): AuthError {
  const detail = typeof data.detail === 'string' ? data.detail : undefined;
  switch (status) {
    case 401:
      return new AuthError('invalid_credentials', detail || 'Invalid email or password.', status);
    case 403:
      return new AuthError(
        'account_not_active',
        detail || 'Your account is not active yet. Please verify your email.',
        status,
      );
    case 409:
      return new AuthError('duplicate_email', detail || 'An account with this email already exists.', status);
    case 422:
      return new AuthError('validation', detail || 'Please check the details you entered.', status);
    case 429:
      return new AuthError('account_locked', detail || 'Account temporarily locked. Try again in 15 minutes.', status);
    default:
      return new AuthError('unknown', detail || 'Something went wrong. Please try again.', status);
  }
}

/**
 * POST helper. Returns the parsed JSON on a 2xx response.
 * Throws AuthError on an HTTP error status.
 * Throws the special NETWORK_FALLBACK marker when the backend is unreachable,
 * so callers can drop to the mock.
 */
const NETWORK_FALLBACK = Symbol('network-fallback');

async function postJson(path: string, body: unknown): Promise<Record<string, unknown>> {
  if (!API_BASE) throw NETWORK_FALLBACK;

  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(body),
    });
  } catch {
    // Network/CORS failure -> backend not reachable -> fall back to mock.
    throw NETWORK_FALLBACK;
  }

  if (!res.ok) throw errorForResponse(res.status, await safeJson(res));
  return safeJson(res);
}

// ---------------------------------------------------------------------------
// In-browser mock (used standalone or when the API is unreachable)
// ---------------------------------------------------------------------------

let mockFailedAttempts = 0;

async function mockLogin(email: string, password: string): Promise<LoginResult> {
  await delay(900);

  // Simulate the lockout path (AC-AUTH-06 / EC-AUTH-LGN-02).
  if (mockFailedAttempts >= MOCK_LOCKOUT_THRESHOLD) {
    throw new AuthError('account_locked', 'Account temporarily locked. Try again in 15 minutes.', 429);
  }

  const ok = email.trim().toLowerCase() === DEMO_EMAIL && password === DEMO_PASSWORD;
  if (!ok) {
    mockFailedAttempts += 1;
    if (mockFailedAttempts >= MOCK_LOCKOUT_THRESHOLD) {
      throw new AuthError('account_locked', 'Account temporarily locked. Try again in 15 minutes.', 429);
    }
    throw new AuthError('invalid_credentials', 'Invalid email or password.', 401);
  }

  mockFailedAttempts = 0;
  return { accessToken: 'mock.jwt.token', tokenType: 'bearer', mocked: true };
}

async function mockRegister(email: string): Promise<RegisterResult> {
  await delay(1100);
  if (email.trim().toLowerCase() === DEMO_EMAIL) {
    throw new AuthError('duplicate_email', 'An account with this email already exists.', 409);
  }
  return { message: 'Account created. Check your inbox to verify your email.', mocked: true };
}

async function mockResetRequest(): Promise<ResetResult> {
  await delay(600);
  // Enumeration-safe: always the same response (AC-AUTH-10).
  return { message: 'If an account exists for this email, a reset link has been sent.', mocked: true };
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

export const authClient = {
  /** POST /auth/login — returns an access token on success. */
  async login(email: string, password: string): Promise<LoginResult> {
    try {
      const data = await postJson('/auth/login', { email, password });
      return {
        accessToken: String(data.access_token ?? ''),
        tokenType: String(data.token_type ?? 'bearer'),
        mocked: false,
      };
    } catch (err) {
      if (err === NETWORK_FALLBACK) return mockLogin(email, password);
      throw err;
    }
  },

  /** POST /auth/register — creates a PENDING_VERIFICATION account. */
  async register(input: { name: string; email: string; password: string }): Promise<RegisterResult> {
    try {
      const data = await postJson('/auth/register', input);
      return {
        message: String(data.message ?? 'Account created. Check your inbox to verify your email.'),
        mocked: false,
      };
    } catch (err) {
      if (err === NETWORK_FALLBACK) return mockRegister(input.email);
      throw err;
    }
  },

  /** POST /auth/password-reset/request — always enumeration-safe (HTTP 202). */
  async requestPasswordReset(email: string): Promise<ResetResult> {
    try {
      const data = await postJson('/auth/password-reset/request', { email });
      return {
        message: String(data.message ?? 'If an account exists for this email, a reset link has been sent.'),
        mocked: false,
      };
    } catch (err) {
      if (err === NETWORK_FALLBACK) return mockResetRequest();
      // Reset is fire-and-forget; never surface an error to the user.
      return mockResetRequest();
    }
  },

  /** Whether the client is configured to talk to a real backend. */
  get usingApi(): boolean {
    return Boolean(API_BASE);
  },
};
