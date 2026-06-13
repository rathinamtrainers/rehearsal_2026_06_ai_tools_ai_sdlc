/**
 * LearnFlow password complexity rules (per UC-1 §2.1 / EC-AUTH-REG-04/05):
 * at least 8 characters, 1 uppercase, 1 digit, 1 special character.
 * `scorePassword` returns how many of the four rules are met (0..4); a score of
 * 4 is the registration pass mark. Shared by the strength meter and form
 * validation so the UI and the rules never drift apart.
 */
export const PASSWORD_RULES = {
  minLength: 8,
} as const

export const PASSWORD_HELPER =
  'At least 8 characters, with 1 uppercase, 1 number and 1 special character.'

const SPECIAL = /[!@#$%^&*(),.?":{}|<>_\-[\]\\/+=;'`~]/

export function scorePassword(pw = ''): number {
  const checks = [
    pw.length >= PASSWORD_RULES.minLength,
    /[A-Z]/.test(pw),
    /[0-9]/.test(pw),
    SPECIAL.test(pw),
  ]
  return checks.filter(Boolean).length // 0..4
}

export function passwordMeetsRules(pw: string): boolean {
  return scorePassword(pw) === 4
}
