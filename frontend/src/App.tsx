/**
 * Auth flow orchestrator — a small client-side state machine over the six auth
 * screens (login, register, verify, forgot, forgot-sent, login-success), wired to
 * the typed auth API client (real FastAPI /auth/* with a standalone mock fallback).
 *
 * Email is the sole identifier; there is no social/SSO. Login surfaces the
 * invalid-credentials (401) and lockout (429) states; register validates the
 * LearnFlow complexity rules client-side and routes to email verification;
 * forgot-password routes to the enumeration-safe "reset link sent" terminal.
 */
import { useState, type ChangeEvent, type FormEvent } from 'react'
import { AuthShell } from './screens/AuthShell'
import { LoginScreen, type FormError } from './screens/LoginScreen'
import { RegisterScreen } from './screens/RegisterScreen'
import { VerifyEmailScreen } from './screens/VerifyEmailScreen'
import { ForgotPasswordScreen } from './screens/ForgotPasswordScreen'
import { ForgotSentScreen } from './screens/ForgotSentScreen'
import { LoginSuccessScreen } from './screens/LoginSuccessScreen'
import { AuthError, authMode, login, register, requestPasswordReset } from './api/auth'
import { passwordMeetsRules } from './lib/password'

type Screen = 'login' | 'register' | 'verify' | 'forgot' | 'forgotSent' | 'loginSuccess'

const EMAIL_RE = /\S+@\S+\.\S+/

export default function App() {
  const [screen, setScreen] = useState<Screen>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [remember, setRemember] = useState(true)
  const [agree, setAgree] = useState(false)

  const [touched, setTouched] = useState(false) // register: show field errors after first submit
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<FormError | null>(null) // login-level Alert
  const [serverEmailError, setServerEmailError] = useState('') // register: e.g. duplicate email
  const [resent, setResent] = useState(false) // verify: resend confirmation

  /** Navigate, resetting the per-screen transient flags (mirrors the prototype's nav). */
  function nav(next: Screen) {
    setScreen(next)
    setLoading(false)
    setTouched(false)
    setError(null)
    setServerEmailError('')
    setResent(false)
  }

  const onEmail = (e: ChangeEvent<HTMLInputElement>) => {
    setEmail(e.target.value)
    setServerEmailError('')
  }
  const onPassword = (e: ChangeEvent<HTMLInputElement>) => setPassword(e.target.value)
  const onName = (e: ChangeEvent<HTMLInputElement>) => setName(e.target.value)
  const onRemember = (e: ChangeEvent<HTMLInputElement>) => setRemember(e.target.checked)
  const onAgree = (e: ChangeEvent<HTMLInputElement>) => setAgree(e.target.checked)

  const emailDisplay = email || 'you@example.com'

  // ---- Submit handlers --------------------------------------------------

  async function submitLogin(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await login({ email, password, remember })
      nav('loginSuccess')
    } catch (err) {
      const message =
        err instanceof AuthError ? err.message : 'Something went wrong. Please try again.'
      const tone = err instanceof AuthError ? err.tone : 'danger'
      setError({ message, tone })
      setLoading(false)
    }
  }

  async function submitRegister(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setTouched(true)
    const ok = name.trim() !== '' && EMAIL_RE.test(email) && passwordMeetsRules(password) && agree
    if (!ok) return
    setLoading(true)
    try {
      await register({ name, email, password })
      nav('verify')
    } catch (err) {
      // Surface a duplicate-email (409) under the email field; keep the user here.
      setServerEmailError(
        err instanceof AuthError ? err.message : 'Could not create your account. Please try again.',
      )
      setLoading(false)
    }
  }

  async function submitForgot(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setLoading(true)
    await requestPasswordReset(email) // always resolves (enumeration-safe)
    nav('forgotSent')
  }

  // ---- Register field errors (shown only after first submit) ------------

  const registerErrors = {
    name: touched && name.trim() === '' ? 'Please enter your name.' : '',
    email:
      serverEmailError ||
      (touched && !EMAIL_RE.test(email) ? 'Enter a valid email address.' : ''),
    password: touched && !passwordMeetsRules(password) ? 'Password does not meet the requirements.' : '',
  }

  // ---- Render -----------------------------------------------------------

  return (
    <AuthShell>
      {screen === 'login' && (
        <LoginScreen
          email={email}
          password={password}
          remember={remember}
          loading={loading}
          error={error}
          showMockHint={authMode === 'mock'}
          onEmail={onEmail}
          onPassword={onPassword}
          onRemember={onRemember}
          onDismissError={() => setError(null)}
          onSubmit={submitLogin}
          onForgot={() => nav('forgot')}
          onRegister={() => nav('register')}
        />
      )}

      {screen === 'register' && (
        <RegisterScreen
          name={name}
          email={email}
          password={password}
          agree={agree}
          loading={loading}
          errors={registerErrors}
          onName={onName}
          onEmail={onEmail}
          onPassword={onPassword}
          onAgree={onAgree}
          onSubmit={submitRegister}
          onLogin={() => nav('login')}
        />
      )}

      {screen === 'verify' && (
        <VerifyEmailScreen
          emailDisplay={emailDisplay}
          resent={resent}
          onResend={() => setResent(true)}
          onLogin={() => nav('login')}
          onBackToRegister={() => nav('register')}
        />
      )}

      {screen === 'forgot' && (
        <ForgotPasswordScreen
          email={email}
          loading={loading}
          onEmail={onEmail}
          onSubmit={submitForgot}
          onBackToLogin={() => nav('login')}
        />
      )}

      {screen === 'forgotSent' && (
        <ForgotSentScreen emailDisplay={emailDisplay} onBackToLogin={() => nav('login')} />
      )}

      {screen === 'loginSuccess' && (
        <LoginSuccessScreen emailDisplay={emailDisplay} onLogout={() => nav('login')} />
      )}
    </AuthShell>
  )
}
