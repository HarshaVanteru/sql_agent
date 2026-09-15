import { DatabaseIcon } from '@/components/icons/DatabaseIcon';
import { TrashIcon } from '@/components/icons/TrashIcon';
import { IconButton } from '@/components/ui';
import { cn } from '@/lib/cn';
import { DATABASE_LABELS, type Connection } from '@/types';

interface ConnectionItemProps {
  connection: Connection;
  selected: boolean;
  onSelect: (connectionId: string) => void;
  onDelete: (connectionId: string) => void;
  deleting: boolean;
}

export function ConnectionItem({
  connection,
  selected,
  onSelect,
  onDelete,
  deleting,
}: ConnectionItemProps) {
  return (
    <div
      className={cn(
        'group flex items-center gap-2 rounded px-2 py-1.5',
        selected ? 'bg-signal-wash' : 'hover:bg-paper',
      )}
    >
      <button
        type="button"
        onClick={() => onSelect(connection.id)}
        aria-current={selected ? 'true' : undefined}
        className="flex min-w-0 flex-1 items-center gap-2.5 text-left focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-signal"
      >
        <DatabaseIcon className={cn('h-4 w-4 shrink-0', selected ? 'text-signal' : 'text-muted')} />
        <span className="min-w-0 flex-1">
          <span className={cn('block truncate text-sm', selected ? 'font-medium text-ink' : 'text-ink')}>
            {connection.name}
          </span>
          <span className="block truncate text-xs text-slate">
            {DATABASE_LABELS[connection.dbType] ?? connection.dbType}
          </span>
        </span>
      </button>
      <IconButton
        label={`Remove ${connection.name}`}
        tone="danger"
        disabled={deleting}
        onClick={() => onDelete(connection.id)}
        className="opacity-0 group-hover:opacity-100 focus-visible:opacity-100"
      >
        <TrashIcon />
      </IconButton>
    </div>
  );
}
