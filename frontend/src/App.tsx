import { Suspense, lazy } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';

import { Spinner } from '@/components/ui';
import { LandingPage } from '@/pages/LandingPage';
import { NotFoundPage } from '@/pages/NotFoundPage';
import { RequireSession } from '@/routes/RequireSession';

/**
 * Split from the landing page.
 *
 * The workspace carries the markdown renderer, which is most of the
 * JavaScript on the page and is worth nothing to a visitor who has not started
 * a session yet. They get the smaller half; the rest loads while the session
 * is being created.
 */
const WorkspacePage = lazy(() =>
  import('@/pages/WorkspacePage').then((m) => ({ default: m.WorkspacePage })),
);

function PageLoading() {
  return (
    <div className="flex min-h-dvh items-center justify-center bg-paper">
      <Spinner className="text-muted" />
    </div>
  );
}

export function App() {
  return (
    <Suspense fallback={<PageLoading />}>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route element={<RequireSession />}>
          <Route path="/workspace" element={<WorkspacePage />} />
        </Route>
        <Route path="/app" element={<Navigate to="/workspace" replace />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </Suspense>
  );
}
