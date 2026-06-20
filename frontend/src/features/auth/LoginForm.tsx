import { useState } from 'react';
import type { FormEvent, MouseEvent } from 'react';
import { Alert } from '../../components/Alert';
import { Button } from '../../components/Button';
import { Checkbox } from '../../components/Checkbox';
import { Input } from '../../components/Input';
import { PasswordInput } from '../../components/PasswordInput';
import { MailIcon, LockIcon } from '../../lib/icons';
import { emailOk } from '../../lib/validation';
import { authClient, AuthError } from '../../api/authClient';

const linkStyle = { color: 'var(--text-link)', fontWeight: 600, textDecoration: 'none' } as const;

export function LoginForm({ onGoToRegister }: { onGoToRegister: () => void }) {
  const [email, setEmail] = useState('learner@example.com');
  const [password, setPassword] = useState('Password1!');
  const [remember, setRemember] = useState(true);

  const [submitted, setSubmitted] = useState(false);
  const [touchedEmail, setTouchedEmail] = useState(false);
  const [touchedPw, setTouchedPw] = useState(false);

  const [loading, setLoading] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [resetSent, setResetSent] = useState(false);

  const emailErr =
    touchedEmail || submitted
      ? !email.trim()
        ? 'Email is required.'
        : !emailOk(email)
          ? 'Enter a valid email address.'
          : undefined
      : undefined;
  const pwErr = touchedPw || submitted ? (!password ? 'Password is required.' : undefined) : undefined;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitted(true);
    setResetSent(false);
    if (!emailOk(email) || !password) return;

    setLoading(true);
    setAuthError(null);
    try {
      await authClient.login(email.trim(), password);
      setSuccess(true);
    } catch (err) {
      setAuthError(err instanceof AuthError ? err.message : 'Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  async function onForgot(e: MouseEvent) {
    e.preventDefault();
    setAuthError(null);
    // Fire enumeration-safe reset request; show the info banner regardless.
    void authClient.requestPasswordReset(email.trim());
    setResetSent(true);
  }

  return (
    <form onSubmit={onSubmit} style={{ width: '100%', animation: 'lf-fade-up var(--duration-slow) var(--ease-out)' }}>
      <h2
        style={{
          fontSize: 28,
          fontWeight: 700,
          letterSpacing: '-0.01em',
          color: 'var(--text-strong)',
          margin: '0 0 8px',
        }}
      >
        Welcome back
      </h2>
      <p style={{ fontSize: 16, color: 'var(--text-muted)', margin: '0 0 26px' }}>Log in to continue learning.</p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {success && (
          <Alert tone="success" title="You're in">
            Welcome back — taking you to your dashboard…
          </Alert>
        )}
        {authError && (
          <Alert tone="danger" onClose={() => setAuthError(null)}>
            {authError}
          </Alert>
        )}
        {resetSent && (
          <Alert tone="info" onClose={() => setResetSent(false)}>
            If an account exists for that email, a reset link is on its way.
          </Alert>
        )}

        <Input
          label="Email address"
          type="email"
          placeholder="you@example.com"
          iconLeft={<MailIcon />}
          autoComplete="email"
          required
          value={email}
          onChange={(e) => {
            setEmail(e.target.value);
            setAuthError(null);
          }}
          onBlur={() => setTouchedEmail(true)}
          error={emailErr}
        />

        <PasswordInput
          label="Password"
          iconLeft={<LockIcon />}
          autoComplete="current-password"
          required
          value={password}
          onChange={(e) => {
            setPassword(e.target.value);
            setAuthError(null);
          }}
          onBlur={() => setTouchedPw(true)}
          error={pwErr}
        />

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Checkbox label="Remember me" checked={remember} onChange={(e) => setRemember(e.target.checked)} />
          <a href="#" onClick={onForgot} style={{ ...linkStyle, fontSize: 14 }}>
            Forgot password?
          </a>
        </div>

        <Button block size="lg" type="submit" loading={loading}>
          Log in
        </Button>
      </div>

      <p style={{ fontSize: 13, color: 'var(--text-subtle)', textAlign: 'center', margin: '14px 0 0' }}>
        Demo credentials are pre-filled — just press Log in.
      </p>
      <p style={{ fontSize: 14, color: 'var(--text-muted)', textAlign: 'center', margin: '22px 0 0' }}>
        New to LearnFlow?{' '}
        <a
          href="#"
          onClick={(e) => {
            e.preventDefault();
            onGoToRegister();
          }}
          style={linkStyle}
        >
          Create an account
        </a>
      </p>
    </form>
  );
}
