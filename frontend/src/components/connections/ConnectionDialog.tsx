import { useEffect, useMemo } from 'react';

import { Button, Modal } from '@/components/ui';
import { useCreateConnection } from '@/hooks/useConnections';
import type { Connection } from '@/types';
import { ConnectionForm } from './ConnectionForm';
import { pickSampleConnections } from './sampleConnections';
import { useConnectionDraft } from './useConnectionDraft';

const FORM_ID = 'connect-database-form';

interface ConnectionDialogProps {
  open: boolean;
  onClose: () => void;
  onConnected: (connection: Connection) => void;
}

export function ConnectionDialog({ open, onClose, onConnected }: ConnectionDialogProps) {
  const form = useConnectionDraft();

  // Keyed on `open` rather than shuffled in the effect below: an effect runs
  // after the first render, so the dialog painted the previous open's three
  // and swapped them a frame later. useMemo computes during render, so the
  // pills are right the first time they are drawn -- and stable afterwards,
  // rather than reshuffling under the pointer on every keystroke.
  const samples = useMemo(() => pickSampleConnections(), [open]);
  const { reset, applyServerError, trimmed } = form;

  const create = useCreateConnection((connection) => {
    onConnected(connection);
    onClose();
  });

  // A dialog reopened after a failure should not still show the old error, or
  // the credentials of the last attempt.
  useEffect(() => {
    if (open) {
      reset();
      create.reset();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  return (
    <Modal
      open={open}
      title="Connect a database"
      description="Read-only credentials, checked before anything is saved."
      onClose={onClose}
      footer={
        <div className="flex items-center justify-end gap-2">
          <Button type="button" variant="secondary" onClick={onClose} disabled={create.isPending}>
            Cancel
          </Button>
          {/* Outside the <form>, so `form` ties it back to one. That is what
              lets the button sit in the pinned footer while the fields scroll. */}
          <Button type="submit" form={FORM_ID} loading={create.isPending}>
            {create.isPending ? 'Connecting' : 'Connect'}
          </Button>
        </div>
      }
    >
      <ConnectionForm
        form={form}
        formId={FORM_ID}
        samples={samples}
        pending={create.isPending}
        error={create.error}
        onSubmit={() => create.mutate(trimmed, { onError: applyServerError })}
      />
    </Modal>
  );
}
