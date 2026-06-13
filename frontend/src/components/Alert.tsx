/**
 * LearnFlow inline Alert / banner for form-level feedback. Tones map to the API
 * response classes in the auth flows (success, danger, warning, info) — e.g. the
 * danger tone carries the "Invalid email or password." 401 state and the warning
 * tone carries the "Account temporarily locked." 429 state.
 */
import type { ReactNode } from 'react'

type Tone = 'success' | 'danger' | 'warning' | 'info'

type AlertProps = {
  tone?: Tone
  title?: string
  children?: ReactNode
  onClose?: () => void
}

const TONES: Record<Tone, { surface: string; fg: string; dot: string }> = {
  success: { surface: 'bg-success-bg border-success-border', fg: 'text-success-700', dot: 'bg-success' },
  danger: { surface: 'bg-danger-bg border-danger-border', fg: 'text-danger-700', dot: 'bg-danger' },
  warning: { surface: 'bg-warning-bg border-warning-border', fg: 'text-warning-700', dot: 'bg-warning' },
  info: { surface: 'bg-info-bg border-info-border', fg: 'text-info-700', dot: 'bg-info' },
}

const DEFAULT_ICON_PATH: Record<Tone, string> = {
  success: 'M5 10.5 L8.5 14 L15 6',
  danger: 'M10 6 V11 M10 14 h0.01',
  warning: 'M10 6 V11 M10 14 h0.01',
  info: 'M10 9 V14 M10 6 h0.01',
}

export function Alert({ tone = 'info', title, children, onClose }: AlertProps) {
  const t = TONES[tone]
  return (
    <div role="alert" className={['flex items-start gap-2.5 rounded-md border p-3', t.surface].join(' ')}>
      <span className={['mt-px inline-flex size-5 shrink-0 items-center justify-center rounded-full', t.dot].join(' ')}>
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
          <path d={DEFAULT_ICON_PATH[tone]} stroke="#fff" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </span>
      <div className="min-w-0 flex-1">
        {title && <div className={['text-sm font-semibold', t.fg, children ? 'mb-0.5' : ''].join(' ')}>{title}</div>}
        {children && <div className={['text-sm leading-normal', t.fg].join(' ')}>{children}</div>}
      </div>
      {onClose && (
        <button
          type="button"
          onClick={onClose}
          aria-label="Dismiss"
          className={['shrink-0 cursor-pointer border-none bg-transparent p-0.5 leading-none', t.fg].join(' ')}
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
            <path d="M4 4 L12 12 M12 4 L4 12" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
          </svg>
        </button>
      )}
    </div>
  )
}
