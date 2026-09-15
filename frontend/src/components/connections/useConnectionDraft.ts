import { useCallback, useMemo, useState } from 'react';

import { useFormValidation, type RuleMap } from '@/hooks/useFormValidation';
import { errorFields, isApiError } from '@/lib/ApiError';
import { hostname, maxLength, port, required } from '@/lib/validation';
import { DEFAULT_PORTS, type ConnectionDraft, type DatabaseType } from '@/types';

const EMPTY: ConnectionDraft = {
  name: '',
  dbType: 'postgresql',
  host: '',
  port: DEFAULT_PORTS.postgresql,
  username: '',
  password: '',
  databaseName: '',
};

/**
 * Rules mirroring the backend's, so the common mistakes are caught before a
 * round trip. The server still checks everything -- this is for speed of
 * feedback, not for trust.
 *
 * Password has no rule on purpose: public read-only databases are routinely
 * published with a username and no password, and the backend allows that too.
 */
const RULES: RuleMap<ConnectionDraft> = {
  name: [required('Name'), maxLength(255, 'Name')],
  host: [hostname(), maxLength(255, 'Host')],
  port: [port()],
  username: [required('User'), maxLength(255, 'User')],
  databaseName: [required('Database'), maxLength(255, 'Database')],
};

/** The backend names nested fields by path; the form names them by key. */
const SERVER_FIELD_TO_KEY: Record<string, keyof ConnectionDraft> = {
  name: 'name',
  db_type: 'dbType',
  'credentials.host': 'host',
  'credentials.port': 'port',
  'credentials.username': 'username',
  'credentials.password': 'password',
  'credentials.database_name': 'databaseName',
};

export function useConnectionDraft() {
  const [draft, setDraft] = useState<ConnectionDraft>(EMPTY);
  const validation = useFormValidation(draft, RULES);
  const { clearServerError, setServerErrors } = validation;

  const setField = useCallback(
    <K extends keyof ConnectionDraft>(key: K, value: ConnectionDraft[K]) => {
      setDraft((current) => ({ ...current, [key]: value }));
      // Editing a field answers whatever the server said about it.
      clearServerError(key);
    },
    [clearServerError],
  );

  const setDbType = useCallback(
    (dbType: DatabaseType) => {
      setDraft((current) => ({
        ...current,
        dbType,
        // Move the port to the new engine's default, unless it was typed by hand.
        port: Object.values(DEFAULT_PORTS).includes(current.port) ? DEFAULT_PORTS[dbType] : current.port,
      }));
      clearServerError('port');
    },
    [clearServerError],
  );

  const applySample = useCallback((sample: ConnectionDraft) => {
    setDraft(sample);
    setServerErrors({});
  }, [setServerErrors]);

  const reset = useCallback(() => {
    setDraft(EMPTY);
    setServerErrors({});
  }, [setServerErrors]);

  /** Hang a failed submission's per-field messages on the fields that caused it. */
  const applyServerError = useCallback(
    (error: unknown) => {
      const fields = errorFields(error);
      const mapped: Partial<Record<keyof ConnectionDraft, string>> = {};
      for (const [path, message] of Object.entries(fields)) {
        const key = SERVER_FIELD_TO_KEY[path];
        if (key) mapped[key] = message;
      }

      // A rejected connection is about the credentials as a set, not one field,
      // so it stays a form-level message -- except the host, which the driver
      // can actually single out.
      if (isApiError(error) && error.code === 'CONNECTION_EXISTS') mapped.name = error.message;

      setServerErrors(mapped);
    },
    [setServerErrors],
  );

  const trimmed = useMemo<ConnectionDraft>(
    () => ({
      ...draft,
      name: draft.name.trim(),
      host: draft.host.trim(),
      username: draft.username.trim(),
      databaseName: draft.databaseName.trim(),
    }),
    [draft],
  );

  return { draft, trimmed, setField, setDbType, applySample, applyServerError, reset, ...validation };
}
