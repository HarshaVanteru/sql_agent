import { useCallback, useState } from 'react';

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
 * Form state for the connect dialog.
 *
 * Switching engine moves the port to that engine's default, but only when the
 * current value is still a default -- a port someone typed themselves is theirs
 * to keep.
 */
export function useConnectionDraft() {
  const [draft, setDraft] = useState<ConnectionDraft>(EMPTY);

  const setField = useCallback(<K extends keyof ConnectionDraft>(key: K, value: ConnectionDraft[K]) => {
    setDraft((current) => ({ ...current, [key]: value }));
  }, []);

  const setDbType = useCallback((dbType: DatabaseType) => {
    setDraft((current) => ({
      ...current,
      dbType,
      port: Object.values(DEFAULT_PORTS).includes(current.port) ? DEFAULT_PORTS[dbType] : current.port,
    }));
  }, []);

  const reset = useCallback(() => setDraft(EMPTY), []);

  const complete =
    draft.name.trim() !== '' &&
    draft.host.trim() !== '' &&
    draft.username.trim() !== '' &&
    draft.password !== '' &&
    draft.databaseName.trim() !== '' &&
    draft.port > 0;

  return { draft, setField, setDbType, reset, complete };
}
