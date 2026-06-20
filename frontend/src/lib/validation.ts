/**
 * Client-side validation mirroring the LearnFlow auth rules.
 * The backend remains the source of truth (see UC-1 acceptance criteria);
 * these checks just keep the form responsive before submit.
 */

/** Lightweight email shape check (final validation is server-side). */
export function emailOk(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test((email || '').trim());
}

/** Complexity rules: >= 8 chars, 1 uppercase, 1 digit, 1 special char. */
export function pwOk(pw: string): boolean {
  return (
    pw.length >= 8 &&
    /[A-Z]/.test(pw) &&
    /[0-9]/.test(pw) &&
    /[^A-Za-z0-9]/.test(pw)
  );
}
