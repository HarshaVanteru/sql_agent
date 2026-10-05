import { isNumeric } from './formatCell';
import type { QueryResult } from '@/types';

/**
 * Columns whose numbers are labels rather than quantities.
 *
 * Drawing a bar beside `user_id` says that user 900 is "bigger" than user 9,
 * which is nonsense -- and it is nonsense that looks authoritative, which is
 * worse than no chart. Matched on the whole word so `id` and `order_id` are
 * caught but `bid_total` and `video_count` are not.
 */
const IDENTIFIER = /(^|_)(id|ids|key|keys|code|codes|no|num|number|year|month|day|rank|pk|uuid)$/i;

/**
 * Whether a column's numbers are labels rather than quantities.
 *
 * Used for two decisions that turn on the same question. A bar beside
 * `user_id` implies user 900 outranks user 9; grouping its digits into
 * `1,000` implies it was counted. Both dress an identifier up as a
 * measurement.
 */
export function looksLikeIdentifier(column: string): boolean {
  return IDENTIFIER.test(column);
}

export interface ScaleColumn {
  column: string;
  /** The largest value, which the longest bar represents. */
  max: number;
}

/**
 * The one column worth drawing bars for, or null.
 *
 * Deliberately conservative: it only fires when a result is clearly "a label
 * and a measure", which is the shape of nearly every question a person asks of
 * a database in words -- counts by table, revenue by customer, rows by month.
 * Anything more ambiguous gets no bars, because a wrong chart is read as
 * confidently as a right one.
 */
export function scaleColumn(result: QueryResult): ScaleColumn | null {
  if (result.rows.length < 2) return null;

  const firstRow = result.rows[0] ?? {};
  const numeric = result.columns.filter((column) => isNumeric(firstRow[column]));
  // Exactly one measure, and at least one column beside it to name the rows.
  if (numeric.length !== 1 || result.columns.length < 2) return null;

  // `noUncheckedIndexedAccess` is on, and the length check above is not
  // something the compiler carries into the index.
  const column = numeric[0];
  if (column === undefined || looksLikeIdentifier(column)) return null;

  let max = 0;
  let min = Infinity;
  for (const row of result.rows) {
    const value = row[column];
    // One stray null or string and the column is not a clean measure.
    if (!isNumeric(value)) return null;
    // Negatives would need a bar drawn from a baseline in both directions,
    // which is a different chart than the one this draws.
    if (value < 0) return null;
    if (value > max) max = value;
    if (value < min) min = value;
  }

  // Every value identical draws a column of full-width bars, which says
  // nothing at all.
  if (max <= 0 || max === min) return null;
  return { column, max };
}

/** A big number as people say it out loud: 597,371,204 -> "597.4M". */
export function compactNumber(value: number): string {
  return new Intl.NumberFormat([], { notation: 'compact', maximumFractionDigits: 1 }).format(value);
}

/** The sum of a column, for the total shown beside the row count. */
export function sumColumn(result: QueryResult, column: string): number {
  return result.rows.reduce<number>((total, row) => {
    const value = row[column];
    return isNumeric(value) ? total + value : total;
  }, 0);
}
