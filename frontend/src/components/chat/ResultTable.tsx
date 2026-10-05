import { cn } from '@/lib/cn';
import { formatCell, isNumeric } from '@/lib/formatCell';
import { looksLikeIdentifier, scaleColumn } from '@/lib/resultScale';
import type { QueryResult } from '@/types';

interface ResultTableProps {
  result: QueryResult;
}

/**
 * The rows themselves -- the thing the question was asked for.
 *
 * Numeric columns align right so digits line up to be compared, the header
 * stays put while the body scrolls, and the whole table scrolls sideways rather
 * than squeezing columns until nothing is readable.
 *
 * When the result is plainly "a label and a measure" -- which is the shape of
 * most questions asked in words -- a bar is drawn beside the number, so the
 * relationship between the rows is visible without reading nine digits twice.
 * `scaleColumn` decides, and it declines far more often than it agrees.
 */
export function ResultTable({ result }: ResultTableProps) {
  if (result.rows.length === 0) {
    return (
      <p className="px-4 py-6 text-center text-sm text-muted">The query ran and matched nothing.</p>
    );
  }

  // Which columns are numbers is decided once, from the first row, so a column
  // does not flip alignment partway down.
  const firstRow = result.rows[0] ?? {};
  const numericColumns = new Set(result.columns.filter((column) => isNumeric(firstRow[column])));
  // Right-aligned like any number, but printed as written: a primary key of
  // 1000 rendered as "1,000" claims a thousand of something.
  const countedColumns = new Set(
    [...numericColumns].filter((column) => !looksLikeIdentifier(column)),
  );
  const scale = scaleColumn(result);

  return (
    <div className="max-h-[26rem] overflow-auto">
      <table className="w-full border-collapse text-left text-[0.8125rem]">
        <thead className="sticky top-0 z-10 bg-surface">
          <tr>
            {result.columns.map((column) => (
              <th
                key={column}
                scope="col"
                className={cn(
                  'whitespace-nowrap border-b border-rule px-4 py-2 font-mono text-[0.6875rem] font-medium tracking-wide text-muted',
                  numericColumns.has(column) && 'text-right',
                )}
              >
                {column}
              </th>
            ))}
            {scale && (
              <th
                scope="col"
                className="w-40 whitespace-nowrap border-b border-rule px-4 py-2 font-mono text-[0.6875rem] font-medium tracking-wide text-muted"
              >
                relative
              </th>
            )}
          </tr>
        </thead>
        <tbody>
          {result.rows.map((row, rowIndex) => (
            <tr key={rowIndex} className="border-b border-rule/60 last:border-b-0">
              {result.columns.map((column) => {
                const value = row[column];
                const empty = value === null || value === undefined;
                return (
                  <td
                    key={column}
                    className={cn(
                      'max-w-xs truncate px-4 py-2',
                      numericColumns.has(column)
                        ? 'text-right font-mono tabular-nums text-ink'
                        : 'text-ink',
                      empty && 'text-muted',
                    )}
                    title={formatCell(value)}
                  >
                    {countedColumns.has(column) && isNumeric(value)
                      ? value.toLocaleString()
                      : formatCell(value)}
                  </td>
                );
              })}
              {scale && (
                // aria-hidden: the number it draws is in the cell beside it, so
                // announcing a bar as well would read every row twice.
                <td aria-hidden="true" className="px-4 py-2">
                  <span className="block h-1.5 w-full overflow-hidden rounded-full bg-rule/60">
                    <span
                      className="block h-full rounded-full bg-signal-bright"
                      style={{
                        width: `${Math.max(2, (Number(row[scale.column]) / scale.max) * 100)}%`,
                      }}
                    />
                  </span>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
