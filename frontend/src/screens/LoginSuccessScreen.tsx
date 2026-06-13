/**
 * Login success — the terminal shown after a valid login. Stands in for the
 * authenticated dashboard hand-off; "Log out" returns to the login screen.
 */
import { Button } from '../components/Button'
import { CheckCircleIcon } from '../components/icons'

type LoginSuccessScreenProps = {
  emailDisplay: string
  onLogout: () => void
}

export function LoginSuccessScreen({ emailDisplay, onLogout }: LoginSuccessScreenProps) {
  return (
    <div className="lf-screen text-center">
      <div className="mx-auto mb-5 flex size-16 items-center justify-center rounded-xl bg-success-bg text-success">
        <CheckCircleIcon />
      </div>
      <h2 className="mb-2 text-[26px] font-bold text-strong">You're logged in</h2>
      <p className="text-base text-muted">Welcome back — your dashboard is ready.</p>
      <p className="mb-6 text-[15px] font-semibold text-strong">{emailDisplay}</p>
      <Button block size="lg" variant="secondary" onClick={onLogout}>
        Log out
      </Button>
    </div>
  )
}
