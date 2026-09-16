import { MenuIcon } from '@/components/icons/MenuIcon';
import { EndSessionButton } from '@/components/session/EndSessionButton';
import { SessionCountdown } from '@/components/session/SessionCountdown';
import { IconButton } from '@/components/ui';
import type { TimeRemaining } from '@/hooks/useTimeRemaining';

interface AppHeaderProps {
  sessionId: string;
  connectionName: string | null;
  time: TimeRemaining | null;
  onOpenMenu: () => void;
  onEndSession: () => void;
  endingSession: boolean;
}

/**
 * The readable stem of a session id.
 *
 * The server builds ids as `{name-slug}-{unix-seconds}-{random}`, and only the
 * first part means anything to a person -- the rest is what makes the id
 * unguessable, and it is 30 characters of noise across the top of the screen.
 * The full id is still in the URL and in the sidebar footer, which is what you
 * quote when something goes wrong.
 */
function sessionStem(sessionId: string): string {
  const parts = sessionId.split('-');
  return parts.length > 2 ? parts.slice(0, -2).join('-') : sessionId;
}

export function AppHeader({
  sessionId,
  connectionName,
  time,
  onOpenMenu,
  onEndSession,
  endingSession,
}: AppHeaderProps) {
  return (
    <header className="flex h-14 shrink-0 items-center justify-between gap-2 border-b border-rule bg-paper px-3 sm:gap-4 sm:px-5">
      <div className="flex min-w-0 items-center gap-2 sm:gap-2.5">
        <div className="lg:hidden">
          <IconButton label="Open menu" onClick={onOpenMenu}>
            <MenuIcon />
          </IconButton>
        </div>

        {/* A path, not a title: which session, then which database inside it. */}
        <span className="hidden shrink-0 font-serif text-sm italic text-slate sm:inline">
          Session
        </span>
        {/* min-w-0 + truncate, not shrink-0: on a phone the row runs out of
            room and a shrink-0 chip was simply sliced off at the edge, with
            no ellipsis to say the id continued. */}
        <code className="min-w-0 truncate rounded border border-rule bg-raised px-2 py-0.5 font-mono text-[0.75rem] text-ink">
          {sessionStem(sessionId)}
        </code>

        {connectionName && (
          <>
            <span aria-hidden="true" className="hidden text-muted sm:inline">
              /
            </span>
            <span className="hidden min-w-0 items-center gap-1.5 sm:flex">
              <span
                aria-hidden="true"
                className="h-1.5 w-1.5 shrink-0 rounded-full bg-signal-bright"
              />
              <span className="min-w-0 truncate text-[0.8125rem] text-slate">
                {connectionName}
              </span>
            </span>
          </>
        )}
      </div>

      <div className="flex shrink-0 items-center gap-2 sm:gap-3">
        <SessionCountdown time={time} />
        <EndSessionButton onConfirm={onEndSession} pending={endingSession} />
      </div>
    </header>
  );
}
