import { Navigate, Route, Routes } from 'react-router-dom';

import { LandingPage } from '@/pages/LandingPage';
import { NotFoundPage } from '@/pages/NotFoundPage';
import { WorkspacePage } from '@/pages/WorkspacePage';
import { RequireSession } from '@/routes/RequireSession';

export function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route element={<RequireSession />}>
        <Route path="/workspace" element={<WorkspacePage />} />
      </Route>
      <Route path="/app" element={<Navigate to="/workspace" replace />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
