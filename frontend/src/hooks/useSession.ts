import { useQuery } from '@tanstack/react-query';

import { sessionApi } from '@/api';
import { isApiError } from '@/lib/ApiError';
import { queryKeys } from '@/lib/queryKeys';
import type { Session } from '@/types';

/**
 * The current session, or null when there isn't one.
 *
 * A 401 is the ordinary answer for a visitor who has not started yet, so it
 * resolves to null instead of throwing, and is never retried -- retrying a
 * "you have no session" would just be three more of the same reply.
 */
export function useSession() {
  return useQuery<Session | null>({
    queryKey: queryKeys.session,
    queryFn: async () => {
      try {
        return await sessionApi.current();
      } catch (error) {
        if (isApiError(error) && error.isSessionExpired) return null;
        throw error;
      }
    },
    retry: false,
    staleTime: 30_000,
  });
}
