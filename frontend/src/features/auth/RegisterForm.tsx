import { useState } from 'react';
import type { FormEvent, MouseEvent } from 'react';
import { Alert } from '../../components/Alert';
import { Button } from '../../components/Button';
import { Checkbox } from '../../components/Checkbox';
import { Input } from '../../components/Input';
import { PasswordInput } from '../../components/PasswordInput';
import { MailIcon, LockIcon, UserIcon } from '../../lib/icons';
import { emailOk, pwOk } from '../../lib/validation';
import { authClient, AuthError } from '../../api/authClient';

const linkStyle = { color: 'var(--text-link)', fontWeight: 600, textDecoration: 'none' } as const;

export function RegisterForm({ onGoToLogin }: { onGoToLogin: () => void }) {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [agree, setAgree] = useState(false);

  const [submitted, setSubmitted] = useState(false);
  const [touched, setTouched] = useState({ name: false, email: false, pw: false, confirm: false });

  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const t = (k: keyof typeof touched) => touched[k] || submitted;

  const nameErr = t('name') ? (!name.trim() ? 'Enter your name.' : undefined) : undefined;
  const emailErr = t('email')
    ? !email.trim()
      ? 'Email is required.'
      : !emailOk(email)
        ? 'Enter a valid email address.'
        : undefined
    : undefined;
  const pwErr = t('pw')
    ? !password
      ? 'Password is required.'
      : !pwOk(password)
        ? 'Use 8+ characters with an uppercase letter, a number, and a special character.'
        : undefined
    : undefined;
  const confirmErr = t('confirm')
    ? !confirm
      ? 'Re-enter your password.'
      : confirm !== password
        ? 'Passwords don’t match.'
        : undefined
    : undefined;
  const agreeErr = submitted && !agree ? 'Please accept the terms to continue.' : undefined;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitted(true);
    const valid = name.trim() && emailOk(email) && pwOk(password) && confirm === password && agree;
    if (!valid) return;

    setLoading(true);
    setApiError(null);
    try {
      await authClient.register({ name: name.trim(), email: email.trim(), password });
      setSuccess(true);
    } catch (err) {
      setApiError(err instanceof AuthError ? err.message : 'Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  function onResend(e: MouseEvent) {
    e.preventDefault();
    void authClient.requestPasswordReset(email.trim());
  }

  if (success) {
    return (
      <div style={{ width: '100%', textAlign: 'center', animation: 'lf-fade-up var(--duration-slow) var(--ease-out)' }}>
        <div
          style={{
            width: 64,
            height: 64,
            borderRadius: '50%',
            background: 'var(--success-bg)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 20px',
          }}
        >
          <svg
            width="30"
            height="30"
            viewBox="0 0 24 24"
            fill="none"
            stroke="var(--success-600)"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
            <path d="m9 11 3 3L22 4" />
          </svg>
        </div>
        <h2
          style={{
            fontSize: 26,
            fontWeight: 700,
            letterSpacing: '-0.01em',
            color: 'var(--text-strong)',
            margin: '0 0 8px',
          }}
        >
          Check your inbox
        </h2>
        <p style={{ fontSize: 16, lineHeight: 1.6, color: 'var(--text-muted)', margin: '0 0 24px' }}>
          We sent a verification link to <strong style={{ color: 'var(--text-strong)' }}>{email}</strong>. Click it to
          activate your account and start learning.
        </p>
        <Button block size="lg" onClick={onGoToLogin}>
          Back to log in
        </Button>
        <p style={{ fontSize: 14, color: 'var(--text-muted)', textAlign: 'center', margin: '18px 0 0' }}>
          Didn't get the email?{' '}
          <a href="#" onClick={onResend} style={linkStyle}>
            Resend
          </a>
        </p>
      </div>
    );
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
        Create your account
      </h2>
      <p style={{ fontSize: 16, color: 'var(--text-muted)', margin: '0 0 26px' }}>
        Start learning in minutes — it's free to join.
      </p>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {apiError && (
          <Alert tone="danger" onClose={() => setApiError(null)}>
            {apiError}
          </Alert>
        )}

        <Input
          label="Full name"
          placeholder="Priya Nair"
          iconLeft={<UserIcon />}
          autoComplete="name"
          required
          value={name}
          onChange={(e) => setName(e.target.value)}
          onBlur={() => setTouched((s) => ({ ...s, name: true }))}
          error={nameErr}
        />

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
            setApiError(null);
          }}
          onBlur={() => setTouched((s) => ({ ...s, email: true }))}
          error={emailErr}
        />

        <PasswordInput
          label="Password"
          iconLeft={<LockIcon />}
          autoComplete="new-password"
          required
          showStrength
          helper="Must be 8+ characters with an uppercase letter, a number, and a special character."
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          onBlur={() => setTouched((s) => ({ ...s, pw: true }))}
          error={pwErr}
        />

        <PasswordInput
          label="Confirm password"
          iconLeft={<LockIcon />}
          autoComplete="new-password"
          required
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          onBlur={() => setTouched((s) => ({ ...s, confirm: true }))}
          error={confirmErr}
        />

        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          <Checkbox
            label="I agree to LearnFlow's Terms of Service and Privacy Policy."
            checked={agree}
            onChange={(e) => setAgree(e.target.checked)}
          />
          {agreeErr && <span style={{ fontSize: 12, color: 'var(--danger-600)', paddingLeft: 2 }}>{agreeErr}</span>}
        </div>

        <Button block size="lg" type="submit" loading={loading}>
          Create account
        </Button>
      </div>

      <p style={{ fontSize: 14, color: 'var(--text-muted)', textAlign: 'center', margin: '22px 0 0' }}>
        Already have an account?{' '}
        <a
          href="#"
          onClick={(e) => {
            e.preventDefault();
            onGoToLogin();
          }}
          style={linkStyle}
        >
          Log in
        </a>
      </p>
    </form>
  );
}
