import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { connectionsApi } from '@/api';
import { queryKeys } from '@/lib/queryKeys';
import type { Connection, ConnectionDraft } from '@/types';

/** Every database connected in this session. */
export function useConnections(enabled = true) {
  return useQuery<Connection[]>({
    queryKey: queryKeys.connections,
    queryFn: () => connectionsApi.list(),
    enabled,
  });
}

export function useCreateConnection(onCreated?: (connection: Connection) => void) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (draft: ConnectionDraft) => connectionsApi.create(draft),
    onSuccess: (connection) => {
      // Put it in the cache before anything downstream runs. The caller selects
      // the new connection straight away, and a selection that names a
      // connection the cached list does not have yet reads as a stale id -- so
      // without this the workspace clears the selection it was just given.
      queryClient.setQueryData<Connection[]>(queryKeys.connections, (current) =>
        current ? [connection, ...current] : [connection],
      );
      void queryClient.invalidateQueries({ queryKey: queryKeys.connections });
      // The session carries a connection count shown in the header.
      void queryClient.invalidateQueries({ queryKey: queryKeys.session });
      onCreated?.(connection);
    },
  });
}

export function useDeleteConnection(onDeleted?: (connectionId: string) => void) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (connectionId: string) => connectionsApi.remove(connectionId),
    onSuccess: (_result, connectionId) => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.connections });
      void queryClient.invalidateQueries({ queryKey: queryKeys.session });
      // The server drops this connection's conversations with it; the keys nest
      // under the connection, so one removal takes the whole subtree.
      queryClient.removeQueries({ queryKey: ['connections', connectionId] });
      onDeleted?.(connectionId);
    },
  });
}
