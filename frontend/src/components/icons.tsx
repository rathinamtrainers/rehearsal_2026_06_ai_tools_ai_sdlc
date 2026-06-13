/**
 * Stroke icons used across the auth surfaces. Hand-rolled inline SVGs (matching
 * the Lucide-style 1.8px no-fill look the design system specifies) so the UI
 * carries no icon-library dependency. Size defaults to 18px; color inherits via
 * currentColor unless overridden.
 */
import type { SVGProps, ReactNode } from 'react'

type IconProps = { size?: number } & Omit<SVGProps<SVGSVGElement>, 'width' | 'height' | 'viewBox'>

function Svg({ size, strokeWidth = 1.8, children, ...rest }: IconProps & { children: ReactNode }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...rest}
    >
      {children}
    </svg>
  )
}

export function MailIcon({ size = 18, ...rest }: IconProps) {
  return (
    <Svg size={size} {...rest}>
      <rect x="2" y="4" width="20" height="16" rx="2" />
      <path d="m22 7-10 5L2 7" />
    </Svg>
  )
}

export function LockIcon({ size = 18, ...rest }: IconProps) {
  return (
    <Svg size={size} {...rest}>
      <rect x="3" y="11" width="18" height="11" rx="2" />
      <path d="M7 11V7a5 5 0 0 1 10 0v4" />
    </Svg>
  )
}

export function UserIcon({ size = 18, ...rest }: IconProps) {
  return (
    <Svg size={size} {...rest}>
      <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" />
      <circle cx="12" cy="7" r="4" />
    </Svg>
  )
}

export function RefreshIcon({ size = 16, ...rest }: IconProps) {
  return (
    <Svg size={size} {...rest}>
      <path d="M21 2v6h-6" />
      <path d="M3 12a9 9 0 0 1 15-6.7L21 8" />
      <path d="M3 22v-6h6" />
      <path d="M21 12a9 9 0 0 1-15 6.7L3 16" />
    </Svg>
  )
}

export function ArrowLeftIcon({ size = 16, ...rest }: IconProps) {
  return (
    <Svg size={size} {...rest}>
      <path d="M19 12H5" />
      <path d="m12 19-7-7 7-7" />
    </Svg>
  )
}

export function CheckIcon({ size = 15, ...rest }: IconProps) {
  return (
    <Svg size={size} strokeWidth={2.4} {...rest}>
      <path d="M20 6 9 17l-5-5" />
    </Svg>
  )
}

/** Mail-with-check — the "check your inbox" verify glyph. */
export function MailCheckIcon({ size = 30, ...rest }: IconProps) {
  return (
    <Svg size={size} {...rest}>
      <path d="M22 13V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h9" />
      <path d="m2 7 10 5 10-5" />
      <path d="m16 19 2 2 4-4" />
    </Svg>
  )
}

/** Paper-plane — the "reset link sent" glyph. */
export function SendIcon({ size = 28, ...rest }: IconProps) {
  return (
    <Svg size={size} {...rest}>
      <path d="M22 2 11 13" />
      <path d="M22 2 15 22l-4-9-9-4 20-7Z" />
    </Svg>
  )
}

/** Circle-check — the "you're logged in" success glyph. */
export function CheckCircleIcon({ size = 30, ...rest }: IconProps) {
  return (
    <Svg size={size} {...rest}>
      <path d="M21.8 10A10 10 0 1 1 17 3.34" />
      <path d="m9 11 3 3L22 4" />
    </Svg>
  )
}
