/**
 * Password field with a show/hide reveal toggle and an optional strength meter.
 * Strength reflects the LearnFlow registration complexity rules (scorePassword);
 * the four-segment bar and label only appear once the learner starts typing.
 */
import { useState, type ReactNode } from 'react'
import { Input } from './Input'
import { scorePassword } from '../lib/password'

type PasswordInputProps = {
  label?: string
  value: string
  onChange: React.ChangeEventHandler<HTMLInputElement>
  placeholder?: string
  error?: string
  helper?: ReactNode
  showStrength?: boolean
  iconLeft?: ReactNode
  required?: boolean
  autoComplete?: string
}

const LABELS = ['Too weak', 'Weak', 'Fair', 'Good', 'Strong']
// index by score 0..4 — danger, danger, warning, teal, success
const SEG_COLORS = ['bg-danger-500', 'bg-danger-500', 'bg-warning-500', 'bg-teal-500', 'bg-success']
const TEXT_COLORS = ['text-danger-500', 'text-danger-500', 'text-warning-500', 'text-teal-500', 'text-success']

export function PasswordInput({
  label = 'Password',
  value = '',
  onChange,
  placeholder = '••••••••',
  error,
  helper,
  showStrength = false,
  iconLeft = null,
  required = false,
  autoComplete,
}: PasswordInputProps) {
  const [visible, setVisible] = useState(false)
  const score = scorePassword(value)

  const toggle = (
    <button
      type="button"
      onClick={() => setVisible((v) => !v)}
      aria-label={visible ? 'Hide password' : 'Show password'}
      className="cursor-pointer border-none bg-transparent p-0.5 text-xs font-medium text-muted hover:text-body"
    >
      {visible ? 'Hide' : 'Show'}
    </button>
  )

  return (
    <div className="flex w-full flex-col gap-2">
      <Input
        label={label}
        type={visible ? 'text' : 'password'}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        error={error}
        helper={helper}
        iconLeft={iconLeft}
        required={required}
        rightSlot={toggle}
        autoComplete={autoComplete}
      />
      {showStrength && value.length > 0 && (
        <div className="flex flex-col gap-1.5">
          <div className="flex gap-1">
            {[0, 1, 2, 3].map((i) => (
              <span
                key={i}
                className={[
                  'h-1 flex-1 rounded-full transition-colors duration-200',
                  i < score ? SEG_COLORS[score] : 'bg-slate-200',
                ].join(' ')}
              />
            ))}
          </div>
          <span className={['text-xs font-medium', TEXT_COLORS[score]].join(' ')}>{LABELS[score]}</span>
        </div>
      )}
    </div>
  )
}
