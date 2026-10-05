type ClassValue = string | false | null | undefined;

/** Join class names, dropping the falsy branches of a conditional. */
export function cn(...values: ClassValue[]): string {
  return values.filter(Boolean).join(' ');
}
