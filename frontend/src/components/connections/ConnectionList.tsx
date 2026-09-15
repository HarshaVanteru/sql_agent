import { Spinner } from '@/components/ui';
import type { Connection } from '@/types';
import { ConnectionItem } from './ConnectionItem';

interface ConnectionListProps {
  connections: Connection[];
  loading: boolean;
  selectedId: string | null;
  deletingId: string | null;
  onSelect: (connectionId: string) => void;
  onDelete: (connectionId: string) => void;
}

export function ConnectionList({
  connections,
  loading,
  selectedId,
  deletingId,
  onSelect,
  onDelete,
}: ConnectionListProps) {
  if (loading) {
    return (
      <div className="flex justify-center py-6">
        <Spinner className="text-muted" />
      </div>
    );
  }

  if (connections.length === 0) {
    return (
      <p className="px-2 py-3 text-[0.8125rem] leading-relaxed text-slate">
        Connect a database to start asking questions about it.
      </p>
    );
  }

  return (
    <ul className="flex flex-col gap-0.5">
      {connections.map((connection) => (
        <li key={connection.id}>
          <ConnectionItem
            connection={connection}
            selected={connection.id === selectedId}
            deleting={connection.id === deletingId}
            onSelect={onSelect}
            onDelete={onDelete}
          />
        </li>
      ))}
    </ul>
  );
}
