import { useMutation, useQueryClient } from '@tanstack/react-query';

import { sessionApi } from '@/api';

/**
 * End the session.
 *
 * The server deletes the session and everything under it -- connected
 * databases, conversations, the lot. The cache is cleared rather than
 * invalidated so nothing from it can be shown to whoever uses this browser
 * next, even for the moment before a refetch.
 */
export function useEndSession(onEnded?: () => void) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => sessionApi.end(),
    onSettled: () => {
      // onSettled, not onSuccess: if the session was already gone server-side
      // the local copy still has to go.
      queryClient.clear();
      onEnded?.();
    },
  });
}
