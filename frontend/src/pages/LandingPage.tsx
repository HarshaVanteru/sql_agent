import { useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

import { SessionExpiredNotice } from '@/components/session/SessionExpiredNotice';
import { StartSessionForm } from '@/components/session/StartSessionForm';
import { useSession } from '@/hooks/useSession';
import { useStartSession } from '@/hooks/useStartSession';
import { PARAM } from '@/hooks/useAppParams';

/** What actually happens, in the order it happens. */
const STEPS = [
  ['Give a name', 'That starts a session. No account, no password, no email.'],
  ['Connect a database', 'Postgres or MySQL. Credentials are checked before anything is stored.'],
  ['Ask in plain English', 'The agent reads the schema, writes the SQL, and shows you both.'],
  ['Walk away', 'After 24 hours the session and everything in it is deleted.'],
] as const;

export function LandingPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { data: session } = useSession();
  const expired = (location.state as { sessionExpired?: boolean } | null)?.sessionExpired === true;
  const start = useStartSession((created) =>
    navigate(`/workspace?${PARAM.session}=${encodeURIComponent(created.sessionId)}`),
  );

  // Fetch the workspace's code while the name is being typed, so pressing
  // Start goes straight there. It is a separate chunk to keep this page small;
  // without the prefetch that saving costs a spinner at the worst moment.
  useEffect(() => {
    void import('@/pages/WorkspacePage');
  }, []);

  // Someone arriving with a live session should not have to start another.
  useEffect(() => {
    if (session && !expired) {
      navigate(`/workspace?${PARAM.session}=${encodeURIComponent(session.sessionId)}`, {
        replace: true,
      });
    }
  }, [session, expired, navigate]);

  return (
    <main className="min-h-dvh bg-paper">
      <div className="h-[3px] w-full bg-clock" />

      <div className="mx-auto max-w-4xl px-6 py-16 sm:py-24">
        <h1 className="max-w-[14ch] text-display font-bold text-ink">
          Ask your database anything. For 24 hours.
        </h1>

        <p className="mt-6 max-w-prose text-lg leading-relaxed text-slate">
          Connect a Postgres or MySQL database and ask it questions the way you would ask a
          colleague. You get the rows back, and the query that produced them.
        </p>

        <div className="mt-10">
          <SessionExpiredNotice show={expired} />
          <StartSessionForm
            onStart={(name) => start.mutate(name)}
            pending={start.isPending}
            error={start.error}
          />
        </div>

        <ol className="mt-20 border-t border-rule">
          {STEPS.map(([title, detail], index) => (
            <li
              key={title}
              className="grid grid-cols-[2rem_1fr] gap-x-4 border-b border-rule py-5 sm:grid-cols-[3rem_14rem_1fr] sm:gap-x-6"
            >
              <span className="font-mono text-sm text-muted">{index + 1}</span>
              <h2 className="font-semibold text-ink">{title}</h2>
              <p className="col-start-2 max-w-prose text-[0.9375rem] leading-relaxed text-slate sm:col-start-3">
                {detail}
              </p>
            </li>
          ))}
        </ol>

        <p className="mt-10 max-w-prose text-sm leading-relaxed text-slate">
          Connect each database with a read-only account scoped to that one database. The agent is
          blocked from writing, from reading host files, and from reaching other databases — but
          least-privilege credentials are the real safety net.
        </p>
      </div>
    </main>
  );
}
