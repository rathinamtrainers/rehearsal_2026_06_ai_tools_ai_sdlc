/**
 * LearnFlow Button — primary action element.
 * Variants: primary (indigo), secondary (outline), ghost, danger.
 * Sizes: sm (36px), md (44px), lg (52px), plus `block` for full-width (auth forms).
 * Press nudges 1px down; primary deepens indigo-600 -> 700 on hover. No scale-pop.
 */
import type { ButtonHTMLAttributes, ReactNode } from 'react'

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger'
type Size = 'sm' | 'md' | 'lg'

type ButtonProps = {
  children?: ReactNode
  variant?: Variant
  size?: Size
  block?: boolean
  loading?: boolean
  iconLeft?: ReactNode
  iconRight?: ReactNode
} & Omit<ButtonHTMLAttributes<HTMLButtonElement>, 'children'>

const SIZES: Record<Size, string> = {
  sm: 'h-9 px-[14px] text-sm gap-1.5 rounded-sm',
  md: 'h-11 px-[18px] text-sm gap-2 rounded-md',
  lg: 'h-[52px] px-6 text-base gap-2 rounded-md',
}

const VARIANTS: Record<Variant, string> = {
  primary: 'bg-brand text-on-brand border border-transparent shadow-xs hover:bg-brand-hover',
  secondary: 'bg-card text-strong border border-border-strong shadow-xs hover:bg-slate-50',
  ghost: 'bg-transparent text-brand border border-transparent hover:bg-brand-subtle',
  danger: 'bg-danger text-white border border-transparent shadow-xs hover:bg-danger-700',
}

export function Button({
  children,
  variant = 'primary',
  size = 'md',
  block = false,
  loading = false,
  disabled = false,
  iconLeft = null,
  iconRight = null,
  type = 'button',
  className = '',
  ...rest
}: ButtonProps) {
  const isDisabled = disabled || loading
  return (
    <button
      type={type}
      disabled={isDisabled}
      className={[
        'inline-flex items-center justify-center whitespace-nowrap font-semibold tracking-tight',
        'transition-[background,box-shadow,transform] duration-150 ease-[cubic-bezier(0.2,0,0,1)]',
        'active:translate-y-px',
        'focus-visible:outline-none focus-visible:shadow-focus',
        'disabled:cursor-not-allowed disabled:opacity-55',
        block ? 'w-full' : 'w-auto',
        SIZES[size],
        VARIANTS[variant],
        className,
      ].join(' ')}
      {...rest}
    >
      {loading && (
        <span
          aria-hidden="true"
          className="lf-spin inline-block size-[15px] rounded-full border-2 border-current border-t-transparent"
        />
      )}
      {!loading && iconLeft}
      {children}
      {!loading && iconRight}
    </button>
  )
}
