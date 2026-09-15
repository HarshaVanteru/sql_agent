import {
  MutationCache,
  QueryCache,
  QueryClient,
  QueryClientProvider,
} from '@tanstack/react-query';
import { useCallback, useRef, useState, type ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';

import { isApiError } from '@/lib/ApiError';

/**
 * Sets up the cache, and handles the one error that is not a component's
 * business: the session going away.
 *
 * A 401 can arrive from any query or mutation once 24 hours are up, or once
 * the session is ended in another tab. Handling it here means no component has
 * to, and the visitor gets sent back to the start with a reason instead of a
 * page of failed panels. Lives inside the router so it can navigate.
 */
export function QueryProvider({ children }: { children: ReactNode }) {
  const navigate = useNavigate();

  // Through a ref so the handler below is created once but always calls the
  // current navigate.
  const navigateRef = useRef(navigate);
  navigateRef.current = navigate;

  const handleExpiry = useCallback((error: unknown, client: QueryClient) => {
    if (!isApiError(error) || !error.isSessionExpired) return;
    // Nothing from the old session should survive for the next visitor.
    client.clear();
    navigateRef.current('/', { replace: true, state: { sessionExpired: true } });
  }, []);

  const [client] = useState(() => {
    const queryClient: QueryClient = new QueryClient({
      queryCache: new QueryCache({
        onError: (error) => handleExpiry(error, queryClient),
      }),
      mutationCache: new MutationCache({
        onError: (error) => handleExpiry(error, queryClient),
      }),
      defaultOptions: {
        queries: {
          staleTime: 15_000,
          refetchOnWindowFocus: false,
          // A 401 cannot be retried into a session.
          retry: (failureCount, error) =>
            isApiError(error) && error.isSessionExpired ? false : failureCount < 1,
        },
        mutations: { retry: false },
      },
    });
    return queryClient;
  });

  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
