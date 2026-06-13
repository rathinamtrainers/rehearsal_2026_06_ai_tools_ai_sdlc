/**
 * Reset-link-sent — the enumeration-safe confirmation after a reset request.
 * Deliberately says "If an account exists…" and never confirms the address is
 * registered (FR-09 / AC-AUTH-10).
 */
import { Button } from '../components/Button'
import { SendIcon, ArrowLeftIcon } from '../components/icons'

type ForgotSentScreenProps = {
  emailDisplay: string
  onBackToLogin: () => void
}

export function ForgotSentScreen({ emailDisplay, onBackToLogin }: ForgotSentScreenProps) {
  return (
    <div className="lf-screen text-center">
      <div className="mx-auto mb-5 flex size-16 items-center justify-center rounded-xl bg-success-bg text-success">
        <SendIcon />
      </div>
      <h2 className="mb-2 text-[26px] font-bold text-strong">Check your email</h2>
      <p className="mb-6 text-base leading-relaxed text-muted">
        If an account exists for <b className="text-body">{emailDisplay}</b>, we've sent a link to reset your password.
        The link expires in 30 minutes.
      </p>
      <Button block size="lg" variant="secondary" iconLeft={<ArrowLeftIcon />} onClick={onBackToLogin}>
        Back to log in
      </Button>
    </div>
  )
}
