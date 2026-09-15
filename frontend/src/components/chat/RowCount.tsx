import { formatRowCount } from '@/lib/formatCell';

interface RowCountProps {
  count: number;
  /** True when the backend capped what it fetched. */
  capped?: boolean;
}

export function RowCount({ count, capped = false }: RowCountProps) {
  return (
    <p className="text-xs text-slate">
      {formatRowCount(count)}
      {capped && ' (capped)'}
    </p>
  );
}
