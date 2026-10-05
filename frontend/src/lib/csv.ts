import { formatCell } from './formatCell';
import type { QueryResult } from '@/types';

/**
 * One CSV field, escaped.
 *
 * Quoted whenever it holds a comma, a quote or a newline, with inner quotes
 * doubled -- RFC 4180. A result set is arbitrary database content, so all
 * three turn up: free-text columns hold commas, JSON columns hold quotes.
 */
function field(value: unknown): string {
  const text = value === null || value === undefined ? '' : formatCell(value);
  return /[",\n\r]/.test(text) ? `"${text.replaceAll('"', '""')}"` : text;
}

export function toCsv(result: QueryResult): string {
  const header = result.columns.map(field).join(',');
  const body = result.rows.map((row) => result.columns.map((c) => field(row[c])).join(','));
  return [header, ...body].join('\r\n');
}

/**
 * Hand the rows to the browser as a file.
 *
 * A BOM leads the file because Excel reads a UTF-8 CSV as the local ANSI
 * codepage without one, which turns every accented name in the export into
 * mojibake -- and a spreadsheet is where these files are going.
 */
export function downloadCsv(result: QueryResult, filename: string): void {
  const blob = new Blob([`﻿${toCsv(result)}`], { type: 'text/csv;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename.endsWith('.csv') ? filename : `${filename}.csv`;
  document.body.append(link);
  link.click();
  link.remove();
  // Released on the next tick: revoking synchronously can cancel the download
  // in Safari before it has read the blob.
  setTimeout(() => URL.revokeObjectURL(url), 0);
}
