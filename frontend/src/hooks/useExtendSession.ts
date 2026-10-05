import { useMutation, useQueryClient } from '@tanstack/react-query';

import { sessionApi } from '@/api';
import { queryKeys } from '@/lib/queryKeys';
import type { ExtensionOption } from '@/types';

/**
 * Give the session more time.
 *
 * The response is the session itself with its new expiry, so it goes straight
 * into the cache: the countdown changes the moment the server answers, not
 * after a second round trip to ask again.
 */
export function useExtendSession(onExtended?: () => void) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (duration: ExtensionOption) => sessionApi.extend(duration),
    onSuccess: (session) => {
      queryClient.setQueryData(queryKeys.session, session);
      onExtended?.();
    },
  });
}
