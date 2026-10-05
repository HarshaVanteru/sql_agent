import { Navigate, Outlet, useLocation } from 'react-router-dom';

import { ServiceUnavailable } from '@/components/feedback/ServiceUnavailable';
import { Spinner } from '@/components/ui';
import { useSession } from '@/hooks/useSession';
import { errorMessage, isApiError } from '@/lib/ApiError';

/**
 * Nothing in the workspace renders without a session.
 *
 * The check is the cookie-backed `GET /api/session`, not the `session` search
 * param -- the URL is a bookmark, not a credential, so a link someone was sent
 * lands them here on the start screen.
 */
export function RequireSession() {
  const { data: session, isPending, isFetching, error, refetch } = useSession();
  const location = useLocation();

  if (isPending) {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-paper">
        <Spinner className="text-muted" />
      </div>
    );
  }

  // A backend that is down is not an absent session. Bouncing to the start
  // screen would hide the real problem behind a form that cannot work either.
  if (error && (!isApiError(error) || error.isTemporary)) {
    return (
      <ServiceUnavailable
        message={errorMessage(error, 'The server is not responding.')}
        onRetry={() => void refetch()}
        retrying={isFetching}
      />
    );
  }

  if (!session) return <Navigate to="/" replace state={{ from: location.pathname }} />;

  return <Outlet />;
}
