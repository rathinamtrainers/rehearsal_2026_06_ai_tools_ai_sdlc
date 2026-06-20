import type { CSSProperties } from 'react';

/**
 * Stroke icons used by the auth forms. Mirrors the `icon()` helper in the
 * LearnFlow Auth design: 18px, inherits currentColor, 1.8 stroke weight.
 */
function StrokeIcon({
  size = 18,
  style,
  children,
}: {
  size?: number;
  style?: CSSProperties;
  children: React.ReactNode;
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
      style={style}
      aria-hidden="true"
    >
      {children}
    </svg>
  );
}

export function MailIcon(props: { size?: number; style?: CSSProperties }) {
  return (
    <StrokeIcon {...props}>
      <rect x="2" y="4" width="20" height="16" rx="2" />
      <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
    </StrokeIcon>
  );
}

export function LockIcon(props: { size?: number; style?: CSSProperties }) {
  return (
    <StrokeIcon {...props}>
      <rect x="3" y="11" width="18" height="11" rx="2" />
      <path d="M7 11V7a5 5 0 0 1 10 0v4" />
    </StrokeIcon>
  );
}

export function UserIcon(props: { size?: number; style?: CSSProperties }) {
  return (
    <StrokeIcon {...props}>
      <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" />
      <circle cx="12" cy="7" r="4" />
    </StrokeIcon>
  );
}
