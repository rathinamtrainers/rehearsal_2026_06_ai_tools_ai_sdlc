/**
 * LearnFlow Checkbox with an adjacent label — "Remember me", terms acceptance, etc.
 * The native input is visually hidden; the 18px box fills indigo when checked.
 */
import { useId, type ReactNode } from 'react'

type CheckboxProps = {
  checked: boolean
  onChange: React.ChangeEventHandler<HTMLInputElement>
  label?: ReactNode
  disabled?: boolean
  id?: string
}

export function Checkbox({ checked, onChange, label, disabled = false, id }: CheckboxProps) {
  const reactId = useId()
  const cbId = id ?? reactId
  return (
    <label
      htmlFor={cbId}
      className={[
        'inline-flex items-center gap-2.5 text-sm text-body select-none',
        disabled ? 'cursor-not-allowed opacity-55' : 'cursor-pointer',
      ].join(' ')}
    >
      <span
        className={[
          'inline-flex size-[18px] shrink-0 items-center justify-center rounded-xs border-[1.5px]',
          'transition-[background,border-color] duration-150 ease-[cubic-bezier(0.2,0,0,1)]',
          checked ? 'border-brand bg-brand' : 'border-field bg-card',
        ].join(' ')}
      >
        {checked && (
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
            <path d="M2.5 6.2 L5 8.6 L9.5 3.5" stroke="#fff" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        )}
      </span>
      <input
        id={cbId}
        type="checkbox"
        checked={checked}
        onChange={onChange}
        disabled={disabled}
        className="absolute size-0 opacity-0"
      />
      {label && <span>{label}</span>}
    </label>
  )
}
