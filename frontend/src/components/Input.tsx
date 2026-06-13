/**
 * LearnFlow text Input — label, optional leading icon, helper/error text, and an
 * optional rightSlot (used by PasswordInput for the show/hide toggle). Field is
 * 44px tall, 8px radius; border slate-300 -> indigo-600 + 4px focus ring on focus,
 * red border + red helper on error.
 */
import { useId, useState, type InputHTMLAttributes, type ReactNode } from 'react'

type InputProps = {
  label?: string
  error?: string
  helper?: ReactNode
  iconLeft?: ReactNode
  rightSlot?: ReactNode
} & Omit<InputHTMLAttributes<HTMLInputElement>, 'children'>

export function Input({
  label,
  error,
  helper,
  iconLeft = null,
  rightSlot = null,
  required = false,
  id,
  className = '',
  ...rest
}: InputProps) {
  const [focused, setFocused] = useState(false)
  const reactId = useId()
  const inputId = id ?? reactId
  const invalid = Boolean(error)

  const borderClass = invalid
    ? 'border-danger-500'
    : focused
      ? 'border-brand shadow-focus'
      : 'border-field'

  return (
    <div className={['flex w-full flex-col gap-1.5', className].join(' ')}>
      {label && (
        <label htmlFor={inputId} className="text-sm font-medium text-strong">
          {label}
          {required && <span className="ml-[3px] text-danger-500">*</span>}
        </label>
      )}
      <div
        className={[
          'flex h-11 items-center gap-2 rounded-md border bg-card px-3',
          'transition-[border-color,box-shadow] duration-150 ease-[cubic-bezier(0.2,0,0,1)]',
          borderClass,
        ].join(' ')}
      >
        {iconLeft && <span className="inline-flex shrink-0 text-subtle">{iconLeft}</span>}
        <input
          id={inputId}
          required={required}
          aria-invalid={invalid}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          className="min-w-0 flex-1 border-none bg-transparent text-base text-strong outline-none placeholder:text-subtle"
          {...rest}
        />
        {rightSlot && <span className="inline-flex shrink-0">{rightSlot}</span>}
      </div>
      {(error || helper) && (
        <span className={['inline-flex items-center gap-1 text-xs', invalid ? 'text-danger-700' : 'text-muted'].join(' ')}>
          {error || helper}
        </span>
      )}
    </div>
  )
}
