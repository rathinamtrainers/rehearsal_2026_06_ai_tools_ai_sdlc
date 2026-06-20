import { Logo } from '../../components/Logo';
import { Button } from '../../components/Button';

/**
 * Minimal post-login dashboard placeholder. The LearnFlow Auth design ends at
 * the "You're in" banner; this is the landing surface the login redirects to so
 * the journey completes. Later UCs replace it with the real learner app.
 */
export function Dashboard({ email, onLogout }: { email: string; onLogout: () => void }) {
  const courses = [
    { title: 'Intro to TypeScript', progress: 72, accent: 'var(--indigo-500)' },
    { title: 'React 19 in Practice', progress: 40, accent: 'var(--teal-500)' },
    { title: 'API Design with FastAPI', progress: 15, accent: 'var(--indigo-400)' },
  ];

  return (
    <div style={{ minHeight: '100vh', background: 'var(--surface-page)', fontFamily: 'var(--font-sans)' }}>
      <header
        style={{
          height: 64,
          background: 'var(--surface-card)',
          borderBottom: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 24px',
        }}
      >
        <Logo height={28} />
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <span style={{ fontSize: 14, color: 'var(--text-muted)' }}>{email}</span>
          <Button variant="secondary" size="sm" onClick={onLogout}>
            Log out
          </Button>
        </div>
      </header>

      <main style={{ maxWidth: 960, margin: '0 auto', padding: '40px 24px' }}>
        <h1 style={{ font: 'var(--type-h2)', color: 'var(--text-strong)', margin: '0 0 6px' }}>
          Welcome back 👋
        </h1>
        <p style={{ fontSize: 16, color: 'var(--text-muted)', margin: '0 0 32px' }}>
          You're signed in as <strong style={{ color: 'var(--text-strong)' }}>{email}</strong>. Pick up where you left
          off.
        </p>

        <h2 style={{ font: 'var(--type-h4)', color: 'var(--text-strong)', margin: '0 0 16px' }}>Continue learning</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(260px,1fr))', gap: 20 }}>
          {courses.map((c) => (
            <div
              key={c.title}
              style={{
                background: 'var(--surface-card)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-lg)',
                boxShadow: 'var(--shadow-sm)',
                padding: 20,
              }}
            >
              <div
                style={{
                  height: 96,
                  borderRadius: 'var(--radius-md)',
                  background: `linear-gradient(135deg, ${c.accent}, var(--teal-400))`,
                  marginBottom: 16,
                }}
              />
              <div style={{ fontWeight: 600, color: 'var(--text-strong)', marginBottom: 10 }}>{c.title}</div>
              <div
                style={{
                  height: 6,
                  borderRadius: 'var(--radius-full)',
                  background: 'var(--slate-200)',
                  overflow: 'hidden',
                }}
              >
                <div style={{ width: `${c.progress}%`, height: '100%', background: c.accent }} />
              </div>
              <div style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 8 }}>{c.progress}% complete</div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
