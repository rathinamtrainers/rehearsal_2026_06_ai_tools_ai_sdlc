/**
 * Login — email + password, remember-me, forgot-password link, register cross-link.
 * Renders the invalid-credentials (danger) and account-lockout (warning) error
 * states as a dismissible Alert above the fields. Email is the sole identifier.
 */
import type { ChangeEventHandler, FormEventHandler } from 'react'
import { Input } from '../components/Input'
import { PasswordInput } from '../components/PasswordInput'
import { Checkbox } from '../components/Checkbox'
import { Button } from '../components/Button'
import { Alert } from '../components/Alert'
import { TextLink } from '../components/TextLink'
import { MailIcon, LockIcon } from '../components/icons'
import type { AlertTone } from '../api/auth'

export type FormError = { message: string; tone: AlertTone }

type LoginScreenProps = {
  email: string
  password: string
  remember: boolean
  loading: boolean
  error: FormError | null
  showMockHint: boolean
  onEmail: ChangeEventHandler<HTMLInputElement>
  onPassword: ChangeEventHandler<HTMLInputElement>
  onRemember: ChangeEventHandler<HTMLInputElement>
  onDismissError: () => void
  onSubmit: FormEventHandler<HTMLFormElement>
  onForgot: () => void
  onRegister: () => void
}

export function LoginScreen({
  email,
  password,
  remember,
  loading,
  error,
  showMockHint,
  onEmail,
  onPassword,
  onRemember,
  onDismissError,
  onSubmit,
  onForgot,
  onRegister,
}: LoginScreenProps) {
  return (
    <div className="lf-screen">
      <form onSubmit={onSubmit} noValidate>
        <div className="mb-7">
          <h2 className="mb-2 text-[28px] font-bold tracking-[-0.01em] text-strong">Welcome back</h2>
          <p className="text-base text-muted">Log in to continue learning.</p>
        </div>

        {error && (
          <div className="mb-[18px]">
            <Alert tone={error.tone} onClose={onDismissError}>
              {error.message}
            </Alert>
          </div>
        )}

        <div className="flex flex-col gap-4">
          <Input
            label="Email address"
            type="email"
            placeholder="you@example.com"
            iconLeft={<MailIcon />}
            value={email}
            onChange={onEmail}
            required
            autoComplete="email"
          />
          <div>
            <PasswordInput
              label="Password"
              iconLeft={<LockIcon />}
              value={password}
              onChange={onPassword}
              required
              autoComplete="current-password"
            />
            <div className="mt-3 flex items-center justify-between">
              <Checkbox checked={remember} onChange={onRemember} label="Remember me" />
              <TextLink onClick={onForgot} className="text-sm">
                Forgot password?
              </TextLink>
            </div>
          </div>
          <Button type="submit" block size="lg" loading={loading}>
            Log in
          </Button>
        </div>

        <p className="mt-6 text-center text-sm text-muted">
          New to LearnFlow?{' '}
          <TextLink onClick={onRegister}>Create an account</TextLink>
        </p>
      </form>

      {showMockHint && (
        <div className="mt-7 border-t border-dashed border-border pt-[18px] text-[12.5px] leading-relaxed text-subtle">
          Prototype — try <span className="font-mono text-muted">locked@learnflow.io</span> for the lockout state, or a
          password under 4 characters for an invalid-credentials error.
        </div>
      )}
    </div>
  )
}
