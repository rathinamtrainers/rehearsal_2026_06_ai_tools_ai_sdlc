/**
 * Forgot password — request a reset link by email. The response is always
 * enumeration-safe (the next screen never confirms whether the email exists),
 * per AC-AUTH-10 / FR-09.
 */
import type { ChangeEventHandler, FormEventHandler } from 'react'
import { Input } from '../components/Input'
import { Button } from '../components/Button'
import { TextLink } from '../components/TextLink'
import { MailIcon, ArrowLeftIcon } from '../components/icons'

type ForgotPasswordScreenProps = {
  email: string
  loading: boolean
  onEmail: ChangeEventHandler<HTMLInputElement>
  onSubmit: FormEventHandler<HTMLFormElement>
  onBackToLogin: () => void
}

export function ForgotPasswordScreen({ email, loading, onEmail, onSubmit, onBackToLogin }: ForgotPasswordScreenProps) {
  return (
    <div className="lf-screen">
      <TextLink onClick={onBackToLogin} className="mb-5 inline-flex items-center gap-1.5 text-sm">
        <ArrowLeftIcon /> Back to log in
      </TextLink>
      <form onSubmit={onSubmit} noValidate>
        <div className="mb-7">
          <h2 className="mb-2 text-[28px] font-bold tracking-[-0.01em] text-strong">Forgot your password?</h2>
          <p className="text-base text-muted">Enter your email and we'll send you a link to reset it.</p>
        </div>
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
          <Button type="submit" block size="lg" loading={loading}>
            Send reset link
          </Button>
        </div>
      </form>
    </div>
  )
}
