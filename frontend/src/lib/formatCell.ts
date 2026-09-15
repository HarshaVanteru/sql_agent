/**
 * Render one database value as text.
 *
 * Rows arrive as whatever JSON the driver produced, so every branch here is a
 * shape a real column can have: NULL, a boolean, a JSON column, a number.
 */
export function formatCell(value: unknown): string {
  if (value === null || value === undefined) return '—';
  if (typeof value === 'boolean') return value ? 'true' : 'false';
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}

/** Numbers are read by comparing digits, so they belong on the right. */
export function isNumeric(value: unknown): boolean {
  return typeof value === 'number' && Number.isFinite(value);
}

/** "12 rows", "1 row", "no rows". */
export function formatRowCount(count: number): string {
  if (count === 0) return 'no rows';
  return count === 1 ? '1 row' : `${count.toLocaleString()} rows`;
}
