import { useState } from 'react';

import { ChevronDownIcon } from '@/components/icons/ChevronDownIcon';
import { DatabaseIcon } from '@/components/icons/DatabaseIcon';
import { PlusIcon } from '@/components/icons/PlusIcon';
import { TrashIcon } from '@/components/icons/TrashIcon';
import { IconButton, Spinner } from '@/components/ui';
import { cn } from '@/lib/cn';
import { DATABASE_LABELS, type Connection } from '@/types';

interface TargetDatabaseProps {
  connections: Connection[];
  loading: boolean;
  selectedId: string | null;
  deletingId: string | null;
  onSelect: (connectionId: string) => void;
  onDelete: (connectionId: string) => void;
  onConnect: () => void;
}

/**
 * Which database the next question goes to.
 *
 * A card rather than a list, because at any moment exactly one database is the
 * target and the rest are alternatives. Showing all of them with equal weight
 * made the selected one hard to find, and the selected one is the only thing
 * that changes what a question will do. The others are one click away, under
 * the chevron.
 */
export function TargetDatabase({
  connections,
  loading,
  selectedId,
  deletingId,
  onSelect,
  onDelete,
  onConnect,
}: TargetDatabaseProps) {
  const [open, setOpen] = useState(false);
  const selected = connections.find((connection) => connection.id === selectedId) ?? null;
  const others = connections.filter((connection) => connection.id !== selectedId);

  return (
    <section className="px-4 pb-1 pt-3">
      <header className="flex items-center justify-between pb-1.5">
        <h2 className="text-[0.6875rem] tracking-[0.14em] text-muted">TARGET DATABASE</h2>
        <IconButton label="Connect a database" onClick={onConnect}>
          <PlusIcon />
        </IconButton>
      </header>

      <div className="overflow-hidden rounded-lg border border-rule bg-raised">
        {loading ? (
          <p className="flex items-center gap-2 px-3 py-3 text-sm text-muted">
            <Spinner className="text-muted" />
            Loading databases
          </p>
        ) : selected ? (
          <>
            <div className="flex items-center gap-2.5 px-3 py-2.5">
              <DatabaseIcon className="h-5 w-5 shrink-0 text-signal-bright" />
              <span className="min-w-0 flex-1">
                <span className="block truncate text-sm font-semibold text-ink">
                  {selected.name}
                </span>
                <span className="block truncate font-mono text-[0.6875rem] text-muted">
                  {DATABASE_LABELS[selected.dbType] ?? selected.dbType}
                </span>
              </span>
              {connections.length > 1 && (
                <IconButton
                  label={open ? 'Hide other databases' : 'Switch database'}
                  aria-expanded={open}
                  onClick={() => setOpen((value) => !value)}
                >
                  <ChevronDownIcon
                    className={cn('h-4 w-4 transition-transform', open && 'rotate-180')}
                  />
                </IconButton>
              )}
            </div>

            {open && others.length > 0 && (
              <ul className="border-t border-rule">
                {others.map((connection) => (
                  <li key={connection.id} className="group flex items-center gap-2 px-2 py-1">
                    <button
                      type="button"
                      onClick={() => {
                        onSelect(connection.id);
                        setOpen(false);
                      }}
                      className="flex min-w-0 flex-1 items-center gap-2 rounded px-1 py-1 text-left hover:bg-surface focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-signal"
                    >
                      <DatabaseIcon className="h-4 w-4 shrink-0 text-muted" />
                      <span className="min-w-0 truncate text-sm text-slate">{connection.name}</span>
                    </button>
                    <IconButton
                      label={`Remove ${connection.name}`}
                      tone="danger"
                      disabled={deletingId === connection.id}
                      onClick={() => onDelete(connection.id)}
                      className="opacity-0 group-hover:opacity-100 focus-visible:opacity-100"
                    >
                      <TrashIcon />
                    </IconButton>
                  </li>
                ))}
              </ul>
            )}
          </>
        ) : (
          <button
            type="button"
            onClick={onConnect}
            className="flex w-full items-center gap-2.5 px-3 py-3 text-left hover:bg-signal-faint focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-signal"
          >
            <DatabaseIcon className="h-5 w-5 shrink-0 text-muted" />
            <span className="min-w-0 flex-1">
              <span className="block text-sm font-medium text-ink">No database yet</span>
              <span className="block text-[0.6875rem] text-muted">
                Connect one to start asking
              </span>
            </span>
          </button>
        )}
      </div>
    </section>
  );
}
