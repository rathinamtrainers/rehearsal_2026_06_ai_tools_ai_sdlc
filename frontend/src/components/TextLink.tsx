/**
 * Inline text link rendered as a real <button> — used for the cross-links between
 * auth screens ("Create an account", "Log in", "Forgot password?"). Indigo,
 * semibold, deepens on hover; no underline by default.
 */
import type { ButtonHTMLAttributes, ReactNode } from 'react'

type TextLinkProps = { children: ReactNode } & ButtonHTMLAttributes<HTMLButtonElement>

export function TextLink({ children, className = '', ...rest }: TextLinkProps) {
  return (
    <button
      type="button"
      className={[
        'cursor-pointer border-none bg-transparent p-0 font-semibold text-link hover:text-link-hover',
        'focus-visible:rounded-xs focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand',
        className,
      ].join(' ')}
      {...rest}
    >
      {children}
    </button>
  )
}
