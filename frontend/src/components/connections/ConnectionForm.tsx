import type { FormEvent } from 'react';

import { FormError, TextField } from '@/components/ui';
import { errorMessage, isApiError } from '@/lib/ApiError';
import { DatabaseTypeField } from './DatabaseTypeField';
import { SampleConnectionList } from './SampleConnectionList';
import type { SampleConnection } from './sampleConnections';
import type { useConnectionDraft } from './useConnectionDraft';

type Draft = ReturnType<typeof useConnectionDraft>;

interface ConnectionFormProps {
  form: Draft;
  formId: string;
  samples: readonly SampleConnection[];
  pending: boolean;
  error: unknown;
  onSubmit: () => void;
}

/**
 * A form-level message is for what is wrong with the attempt as a whole -- a
 * refused login, an unreachable host. Anything the server pinned to a single
 * field is shown on that field instead, so it is not said twice.
 */
function formLevelError(error: unknown): string | null {
  if (error == null) return null;
  if (isApiError(error)) {
    if (error.code === 'VALIDATION_ERROR' || error.code === 'CONNECTION_EXISTS') return null;
    if (error.isSessionExpired) return null;
  }
  return errorMessage(error, 'Could not connect.');
}

export function ConnectionForm({ form, formId, samples, pending, error, onSubmit }: ConnectionFormProps) {
  const { draft, setField, setDbType, applySample, errorFor, touch, touchAllAndCheck } = form;

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (touchAllAndCheck()) onSubmit();
  }

  function pickSample(sample: SampleConnection) {
    applySample(sample.draft);
  }

  return (
    <form id={formId} onSubmit={handleSubmit} noValidate className="flex flex-col gap-3.5">
      <SampleConnectionList samples={samples} onPick={pickSample} disabled={pending} />

      <div className="grid grid-cols-2 gap-x-3 gap-y-3">
        <TextField
          id="connection-name"
          label="Name"
          required
          value={draft.name}
          onChange={(event) => setField('name', event.target.value)}
          onBlur={() => touch('name')}
          error={errorFor('name')}
          placeholder="staging analytics"
          disabled={pending}
          maxLength={255}
        />
        <DatabaseTypeField
          value={draft.dbType}
          onChange={setDbType}
          error={errorFor('dbType')}
          disabled={pending}
        />
      </div>

      {/* Host and port are one address, so they share a row -- and a port is
          four characters, so it does not get half the width. */}
      <div className="grid grid-cols-[1fr_5.5rem] gap-x-3">
        <TextField
          id="connection-host"
          label="Host"
          required
          value={draft.host}
          onChange={(event) => setField('host', event.target.value)}
          onBlur={() => touch('host')}
          error={errorFor('host')}
          placeholder="db.example.com"
          disabled={pending}
          autoComplete="off"
          spellCheck={false}
        />
        <TextField
          id="connection-port"
          label="Port"
          required
          type="number"
          inputMode="numeric"
          min={1}
          max={65535}
          value={Number.isNaN(draft.port) ? '' : draft.port}
          onChange={(event) => setField('port', event.target.valueAsNumber)}
          onBlur={() => touch('port')}
          error={errorFor('port')}
          disabled={pending}
        />
      </div>

      <div className="grid grid-cols-2 gap-x-3 gap-y-3">
        <TextField
          id="connection-username"
          label="User"
          required
          value={draft.username}
          onChange={(event) => setField('username', event.target.value)}
          onBlur={() => touch('username')}
          error={errorFor('username')}
          placeholder="readonly"
          disabled={pending}
          autoComplete="off"
          spellCheck={false}
        />
        <TextField
          id="connection-password"
          label="Password"
          type="password"
          value={draft.password}
          onChange={(event) => setField('password', event.target.value)}
          error={errorFor('password')}
          placeholder="Blank if none"
          disabled={pending}
          autoComplete="new-password"
        />
      </div>

      {/* Full width rather than half a row with an empty cell beside it:
          seven fields do not divide into pairs, and this is the one that
          benefits from the room. */}
      <TextField
        id="connection-database"
        label="Database"
        required
        value={draft.databaseName}
        onChange={(event) => setField('databaseName', event.target.value)}
        onBlur={() => touch('databaseName')}
        error={errorFor('databaseName')}
        placeholder="analytics"
        disabled={pending}
        autoComplete="off"
        spellCheck={false}
      />

      <FormError message={formLevelError(error)} />
    </form>
  );
}
