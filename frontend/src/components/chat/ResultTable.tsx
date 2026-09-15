import { cn } from '@/lib/cn';
import { formatCell, isNumeric } from '@/lib/formatCell';
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
 */
export function ResultTable({ result }: ResultTableProps) {
  if (result.rows.length === 0) {
    return (
      <p className="rounded border border-dashed border-rule px-3 py-4 text-center text-sm text-slate">
        The query ran and matched nothing.
      </p>
    );
  }

  // Which columns are numbers is decided once, from the first row, so a column
  // does not flip alignment partway down.
  const firstRow = result.rows[0] ?? {};
  const numericColumns = new Set(result.columns.filter((column) => isNumeric(firstRow[column])));

  return (
    // A table sized to its content: a one-column result stretched to the full
    // width left its heading stranded at one end and the value at the other,
    // reading as a broken table rather than a small one. Wide results still
    // fill the space and scroll sideways inside it.
    // self-start, not inline-block: this sits in a flex column, where a child
    // stretches to the full width and inline-block is ignored entirely.
    <div className="max-h-96 max-w-full self-start overflow-auto rounded border border-rule">
      <table className="w-auto border-collapse text-left font-mono text-[0.8125rem]">
        <thead className="sticky top-0 z-10 bg-surface">
          <tr>
            {result.columns.map((column) => (
              <th
                key={column}
                scope="col"
                className={cn(
                  'whitespace-nowrap border-b border-rule px-3 py-2 font-medium text-slate',
                  numericColumns.has(column) && 'text-right',
                )}
              >
                {column}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {result.rows.map((row, rowIndex) => (
            <tr key={rowIndex} className="border-b border-rule/60 last:border-b-0">
              {result.columns.map((column) => {
                const value = row[column];
                return (
                  <td
                    key={column}
                    className={cn(
                      'max-w-xs truncate px-3 py-1.5 text-ink',
                      numericColumns.has(column) && 'text-right tabular-nums',
                      (value === null || value === undefined) && 'text-muted',
                    )}
                    title={formatCell(value)}
                  >
                    {formatCell(value)}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
