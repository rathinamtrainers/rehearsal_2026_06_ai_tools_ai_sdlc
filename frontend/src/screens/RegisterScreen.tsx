/**
 * Register — full name, email, password (with live strength meter + rule helper),
 * terms acceptance, and a login cross-link. On-submit validation surfaces a
 * field-level error under each control. Email is the sole identifier; no social/SSO.
 */
import type { ChangeEventHandler, FormEventHandler } from 'react'
import { Input } from '../components/Input'
import { PasswordInput } from '../components/PasswordInput'
import { Checkbox } from '../components/Checkbox'
import { Button } from '../components/Button'
import { TextLink } from '../components/TextLink'
import { MailIcon, LockIcon, UserIcon } from '../components/icons'
import { PASSWORD_HELPER } from '../lib/password'

type FieldErrors = { name: string; email: string; password: string }

type RegisterScreenProps = {
  name: string
  email: string
  password: string
  agree: boolean
  loading: boolean
  errors: FieldErrors
  onName: ChangeEventHandler<HTMLInputElement>
  onEmail: ChangeEventHandler<HTMLInputElement>
  onPassword: ChangeEventHandler<HTMLInputElement>
  onAgree: ChangeEventHandler<HTMLInputElement>
  onSubmit: FormEventHandler<HTMLFormElement>
  onLogin: () => void
}

const termsLabel = (
  <span>
    I agree to the <span className="font-semibold text-link">Terms</span> and{' '}
    <span className="font-semibold text-link">Privacy Policy</span>.
  </span>
)

export function RegisterScreen({
  name,
  email,
  password,
  agree,
  loading,
  errors,
  onName,
  onEmail,
  onPassword,
  onAgree,
  onSubmit,
  onLogin,
}: RegisterScreenProps) {
  return (
    <div className="lf-screen">
      <form onSubmit={onSubmit} noValidate>
        <div className="mb-7">
          <h2 className="mb-2 text-[28px] font-bold tracking-[-0.01em] text-strong">Create your account</h2>
          <p className="text-base text-muted">Start learning in under a minute. No card required.</p>
        </div>

        <div className="flex flex-col gap-4">
          <Input
            label="Full name"
            placeholder="Priya Nair"
            iconLeft={<UserIcon />}
            value={name}
            onChange={onName}
            required
            error={errors.name}
            autoComplete="name"
          />
          <Input
            label="Email address"
            type="email"
            placeholder="you@example.com"
            iconLeft={<MailIcon />}
            value={email}
            onChange={onEmail}
            required
            error={errors.email}
            autoComplete="email"
          />
          <PasswordInput
            label="Password"
            iconLeft={<LockIcon />}
            value={password}
            onChange={onPassword}
            required
            showStrength
            helper={PASSWORD_HELPER}
            error={errors.password}
            autoComplete="new-password"
          />
          <Checkbox checked={agree} onChange={onAgree} label={termsLabel} />
          <Button type="submit" block size="lg" loading={loading}>
            Create account
          </Button>
        </div>

        <p className="mt-6 text-center text-sm text-muted">
          Already have an account? <TextLink onClick={onLogin}>Log in</TextLink>
        </p>
      </form>
    </div>
  )
}
