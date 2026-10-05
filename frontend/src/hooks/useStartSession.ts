import { useMutation, useQueryClient } from '@tanstack/react-query';

import { sessionApi } from '@/api';
import { queryKeys } from '@/lib/queryKeys';
import type { Session } from '@/types';

/** Start a session from a name. The cookie comes back on the response. */
export function useStartSession(onStarted?: (session: Session) => void) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (name: string) => sessionApi.start(name),
    onSuccess: (session) => {
      // Seed the cache rather than refetching what we were just handed.
      queryClient.setQueryData(queryKeys.session, session);
      onStarted?.(session);
    },
  });
}
