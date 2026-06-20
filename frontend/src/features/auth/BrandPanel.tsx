import { Logo } from '../../components/Logo';

/**
 * Left-hand brand panel: indigo->teal gradient wash with floating blobs,
 * inverse logo, value proposition, and a social-proof row. Carried over
 * from the LearnFlow Auth design.
 */
export function BrandPanel() {
  return (
    <aside
      style={{
        position: 'relative',
        overflow: 'hidden',
        background: 'linear-gradient(135deg,#4f46e5 0%,#6366f1 45%,#14b8a6 100%)',
        color: '#fff',
        padding: '48px 56px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
      }}
    >
      <div
        style={{
          position: 'absolute',
          width: 460,
          height: 460,
          borderRadius: '50%',
          background: 'rgba(255,255,255,0.10)',
          top: -160,
          right: -120,
          animation: 'lf-blob 9s ease-in-out infinite alternate',
        }}
      />
      <div
        style={{
          position: 'absolute',
          width: 320,
          height: 320,
          borderRadius: '50%',
          background: 'rgba(94,234,212,0.20)',
          bottom: -120,
          left: -80,
          animation: 'lf-blob 11s ease-in-out infinite alternate-reverse',
        }}
      />

      <div style={{ position: 'relative' }}>
        <Logo inverse height={30} />
      </div>

      <div style={{ position: 'relative', maxWidth: 430 }}>
        <h1
          style={{
            fontSize: 46,
            fontWeight: 800,
            letterSpacing: '-0.02em',
            lineHeight: 1.08,
            margin: '0 0 18px',
          }}
        >
          Learn without limits.
        </h1>
        <p style={{ fontSize: 18, lineHeight: 1.65, color: 'rgba(255,255,255,0.88)', margin: '0 0 28px' }}>
          Pick up in-demand skills at your own pace, track your progress, and earn certificates that move your career
          forward.
        </p>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, fontSize: 15, color: 'rgba(255,255,255,0.92)' }}>
          <div style={{ display: 'flex' }}>
            <span style={{ width: 34, height: 34, borderRadius: '50%', background: '#a5b4fc', border: '2px solid #5b53e8' }} />
            <span
              style={{
                width: 34,
                height: 34,
                borderRadius: '50%',
                background: '#5eead4',
                border: '2px solid #5b53e8',
                marginLeft: -12,
              }}
            />
            <span
              style={{
                width: 34,
                height: 34,
                borderRadius: '50%',
                background: '#c7d2fe',
                border: '2px solid #5b53e8',
                marginLeft: -12,
              }}
            />
          </div>
          <span>
            Join <strong style={{ fontWeight: 700 }}>128,000+</strong> learners
          </span>
        </div>
      </div>

      <div style={{ position: 'relative', fontSize: 14, color: 'rgba(255,255,255,0.78)' }}>
        Bank-grade security · DPDPA &amp; GDPR-aligned
      </div>
    </aside>
  );
}
