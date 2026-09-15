import type { FormEvent } from 'react';

import { Button, FormError, TextField } from '@/components/ui';
import { errorMessage } from '@/lib/ApiError';
import type { ConnectionDraft } from '@/types';
import { DatabaseTypeField } from './DatabaseTypeField';

interface ConnectionFormProps {
  draft: ConnectionDraft;
  setField: <K extends keyof ConnectionDraft>(key: K, value: ConnectionDraft[K]) => void;
  setDbType: (dbType: ConnectionDraft['dbType']) => void;
  complete: boolean;
  pending: boolean;
  error: unknown;
  onSubmit: () => void;
  onCancel: () => void;
}

export function ConnectionForm({
  draft,
  setField,
  setDbType,
  complete,
  pending,
  error,
  onSubmit,
  onCancel,
}: ConnectionFormProps) {
  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (complete) onSubmit();
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <TextField
        id="connection-name"
        label="Name it"
        value={draft.name}
        onChange={(event) => setField('name', event.target.value)}
        placeholder="staging analytics"
        disabled={pending}
        maxLength={255}
      />

      <div className="grid grid-cols-2 gap-3">
        <DatabaseTypeField value={draft.dbType} onChange={setDbType} disabled={pending} />
        <TextField
          id="connection-port"
          label="Port"
          type="number"
          inputMode="numeric"
          min={1}
          max={65535}
          value={draft.port}
          onChange={(event) => setField('port', Number(event.target.value))}
          disabled={pending}
        />
      </div>

      <TextField
        id="connection-host"
        label="Host"
        value={draft.host}
        onChange={(event) => setField('host', event.target.value)}
        placeholder="db.example.com"
        disabled={pending}
        autoComplete="off"
      />

      <TextField
        id="connection-database"
        label="Database"
        value={draft.databaseName}
        onChange={(event) => setField('databaseName', event.target.value)}
        placeholder="analytics"
        disabled={pending}
        autoComplete="off"
      />

      <div className="grid grid-cols-2 gap-3">
        <TextField
          id="connection-username"
          label="User"
          value={draft.username}
          onChange={(event) => setField('username', event.target.value)}
          disabled={pending}
          autoComplete="off"
        />
        <TextField
          id="connection-password"
          label="Password"
          type="password"
          value={draft.password}
          onChange={(event) => setField('password', event.target.value)}
          disabled={pending}
          autoComplete="new-password"
        />
      </div>

      <p className="text-[0.8125rem] leading-relaxed text-slate">
        Use an account with read-only access to this one database. The agent is blocked from
        writing, but least-privilege credentials are the real safety net.
      </p>

      <FormError message={error == null ? null : errorMessage(error, 'Could not connect.')} />

      <div className="flex justify-end gap-2 pt-1">
        <Button type="button" variant="secondary" onClick={onCancel} disabled={pending}>
          Cancel
        </Button>
        <Button type="submit" loading={pending} disabled={!complete}>
          Connect
        </Button>
      </div>
    </form>
  );
}
