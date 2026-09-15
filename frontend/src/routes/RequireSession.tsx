import { Navigate, Outlet, useLocation } from 'react-router-dom';

import { Spinner } from '@/components/ui';
import { useSession } from '@/hooks/useSession';

/**
 * Nothing in the workspace renders without a session.
 *
 * The check is the cookie-backed `GET /api/session`, not the `session` search
 * param -- the URL is a bookmark, not a credential, so a link someone was sent
 * lands them here on the start screen.
 */
export function RequireSession() {
  const { data: session, isPending } = useSession();
  const location = useLocation();

  if (isPending) {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-paper">
        <Spinner className="text-muted" />
      </div>
    );
  }

  if (!session) return <Navigate to="/" replace state={{ from: location.pathname }} />;

  return <Outlet />;
}
