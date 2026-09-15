import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState, type ReactNode } from 'react';

import { isApiError } from '@/lib/ApiError';

function createClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 15_000,
        refetchOnWindowFocus: false,
        // A 401 means the session is gone; asking again cannot bring it back.
        retry: (failureCount, error) =>
          !isApiError(error) || !error.isSessionExpired ? failureCount < 1 : false,
      },
      mutations: { retry: false },
    },
  });
}

export function QueryProvider({ children }: { children: ReactNode }) {
  // In state, not module scope: one client per app instance, created once.
  const [client] = useState(createClient);

  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
