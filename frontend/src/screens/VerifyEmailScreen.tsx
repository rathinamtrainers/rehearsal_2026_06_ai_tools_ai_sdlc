/**
 * Verify email — the terminal shown after a successful registration. Per
 * AC-AUTH-01 no JWT is issued yet; the learner must verify before logging in.
 * Offers "Continue to log in", a resend action, and a go-back link.
 */
import { Button } from '../components/Button'
import { Alert } from '../components/Alert'
import { TextLink } from '../components/TextLink'
import { MailCheckIcon, RefreshIcon } from '../components/icons'

type VerifyEmailScreenProps = {
  emailDisplay: string
  resent: boolean
  onResend: () => void
  onLogin: () => void
  onBackToRegister: () => void
}

export function VerifyEmailScreen({ emailDisplay, resent, onResend, onLogin, onBackToRegister }: VerifyEmailScreenProps) {
  return (
    <div className="lf-screen text-center">
      <div className="mx-auto mb-5 flex size-16 items-center justify-center rounded-xl bg-brand-subtle text-brand">
        <MailCheckIcon />
      </div>
      <h2 className="mb-2 text-[26px] font-bold text-strong">Check your inbox</h2>
      <p className="text-base text-muted">We sent a verification link to</p>
      <p className="mb-6 text-[15px] font-semibold text-strong">{emailDisplay}</p>

      {resent && (
        <div className="mb-4 text-left">
          <Alert tone="success">A new verification email is on its way.</Alert>
        </div>
      )}

      <div className="flex flex-col gap-3">
        <Button block size="lg" onClick={onLogin}>
          Continue to log in
        </Button>
        <Button block size="lg" variant="secondary" iconLeft={<RefreshIcon />} onClick={onResend}>
          Resend verification email
        </Button>
      </div>
      <p className="mt-6 text-center text-sm text-muted">
        Wrong address? <TextLink onClick={onBackToRegister}>Go back</TextLink>
      </p>
    </div>
  )
}
