import { useEffect } from 'react';

import { Modal } from '@/components/ui';
import { useCreateConnection } from '@/hooks/useConnections';
import type { Connection } from '@/types';
import { ConnectionForm } from './ConnectionForm';
import { useConnectionDraft } from './useConnectionDraft';

interface ConnectionDialogProps {
  open: boolean;
  onClose: () => void;
  onConnected: (connection: Connection) => void;
}

export function ConnectionDialog({ open, onClose, onConnected }: ConnectionDialogProps) {
  const { draft, setField, setDbType, reset, complete } = useConnectionDraft();
  const create = useCreateConnection((connection) => {
    onConnected(connection);
    onClose();
  });

  // A dialog reopened after a failure should not still be showing the old
  // error, or the credentials of the last attempt.
  useEffect(() => {
    if (open) {
      reset();
      create.reset();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  return (
    <Modal open={open} title="Connect a database" onClose={onClose}>
      <ConnectionForm
        draft={draft}
        setField={setField}
        setDbType={setDbType}
        complete={complete}
        pending={create.isPending}
        error={create.error}
        onSubmit={() => create.mutate(draft)}
        onCancel={onClose}
      />
    </Modal>
  );
}
