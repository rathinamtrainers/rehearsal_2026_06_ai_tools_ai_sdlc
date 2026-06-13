/**
 * Split-screen auth layout: an indigo→teal brand hero on the left (inverse logo,
 * value prop, feature points) and the form panel on white at the right. The hero
 * collapses on small screens, where a compact logo sits above the form instead.
 * The one place a saturated gradient is welcome in the LearnFlow system.
 */
import type { ReactNode } from 'react'
import { Logo } from '../components/Logo'
import { CheckIcon } from '../components/icons'

const FEATURES = [
  '1,200+ expert-led courses',
  'Progress that syncs across devices',
  'Verified certificates on completion',
]

export function AuthShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-card lg:grid lg:grid-cols-[minmax(420px,1fr)_minmax(520px,1.08fr)]">
      {/* ===================== BRAND PANEL ===================== */}
      <aside className="bg-gradient-brand relative hidden flex-col justify-between overflow-hidden px-14 py-12 text-white lg:flex">
        {/* soft decorative orbs */}
        <div className="pointer-events-none absolute -top-[170px] -right-[120px] size-[460px] rounded-full bg-white/10" />
        <div className="pointer-events-none absolute -bottom-[130px] -left-[90px] size-[320px] rounded-full bg-teal-300/20" />

        <div className="relative">
          <Logo inverse height={30} />
        </div>

        <div className="relative max-w-[430px]">
          <h1 className="mb-[18px] text-[44px] leading-[1.1] font-extrabold tracking-[-0.02em]">Learn without limits.</h1>
          <p className="mb-[30px] text-lg leading-[1.65] text-white/90">
            Pick up in-demand skills at your own pace, track your progress, and earn certificates that move your career
            forward.
          </p>
          <ul className="flex flex-col gap-3.5">
            {FEATURES.map((f) => (
              <li key={f} className="flex items-center gap-3 text-[15px] text-white/90">
                <span className="inline-flex size-[26px] shrink-0 items-center justify-center rounded-full bg-white/15">
                  <CheckIcon />
                </span>
                <span>{f}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="relative text-sm text-white/80">Bank-grade security · DPDPA &amp; GDPR-aligned</div>
      </aside>

      {/* ===================== FORM PANEL ===================== */}
      <main className="bg-gradient-aurora flex items-center justify-center px-6 py-12 lg:bg-card lg:bg-none">
        <div className="w-full max-w-[440px]">
          {/* compact logo for the collapsed (mobile) layout */}
          <div className="mb-8 flex justify-center lg:hidden">
            <Logo height={30} />
          </div>
          {children}
        </div>
      </main>
    </div>
  )
}
