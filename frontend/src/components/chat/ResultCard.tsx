import { DownloadIcon } from '@/components/icons/DownloadIcon';
import { IconButton } from '@/components/ui';
import { downloadCsv } from '@/lib/csv';
import { formatRowCount } from '@/lib/formatCell';
import { compactNumber, scaleColumn, sumColumn } from '@/lib/resultScale';
import type { QueryResult } from '@/types';
import { ResultTable } from './ResultTable';

interface ResultCardProps {
  result: QueryResult;
  /** Used to name the downloaded file. */
  connectionName: string;
}

export function ResultCard({ result, connectionName }: ResultCardProps) {
  const scale = scaleColumn(result);
  // Only when there is a single clean measure -- the same test the bars use.
  // Summing an arbitrary numeric column would as often as not add up a set of
  // averages or percentages and present the answer as a fact.
  const total = scale ? sumColumn(result, scale.column) : null;

  const filename = `${connectionName.toLowerCase().replaceAll(/[^a-z0-9]+/g, '-')}-result`;

  return (
    <section className="w-full min-w-0 overflow-hidden rounded-xl border border-rule bg-raised">
      <header className="flex flex-wrap items-center gap-x-3 gap-y-2 border-b border-rule bg-paper px-4 py-2.5">
        <h3 className="font-serif text-[0.9375rem] text-ink">Query results</h3>
        <span className="rounded-full border border-rule bg-raised px-2 py-0.5 font-mono text-[0.6875rem] text-slate">
          {formatRowCount(result.rowCount)}
        </span>

        <div className="ml-auto flex items-center gap-2">
          {total !== null && scale && (
            <span className="rounded-full bg-signal-faint px-2.5 py-0.5 font-mono text-[0.6875rem] text-signal">
              {scale.column} totals {compactNumber(total)}
            </span>
          )}
          {result.rows.length > 0 && (
            <IconButton
              label="Download these rows as CSV"
              onClick={() => downloadCsv(result, filename)}
            >
              <DownloadIcon />
            </IconButton>
          )}
        </div>
      </header>

      <ResultTable result={result} />
    </section>
  );
}
