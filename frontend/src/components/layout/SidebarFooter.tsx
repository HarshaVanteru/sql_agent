import { SignOutIcon } from '@/components/icons/SignOutIcon';
import { Spinner } from '@/components/ui';

interface SidebarFooterProps {
  name: string;
  sessionId: string;
  onEndSession: () => void;
  ending: boolean;
}

/** "Calm_Moss_6490" -> "CM". Two letters is all the circle has room for. */
function initials(name: string): string {
  const parts = name.split(/[\s_-]+/).filter(Boolean);
  const letters = parts.slice(0, 2).map((part) => part[0]);
  return (letters.join('') || '?').toUpperCase();
}

/**
 * Who this session belongs to, pinned to the bottom of the sidebar.
 *
 * There are no accounts here: the name is the one the visitor was given when
 * they arrived, and the id beneath it is the session itself. It is shown
 * because it is the thing to quote when something goes wrong -- it is in the
 * URL and in every log line on the server.
 */
export function SidebarFooter({ name, sessionId, onEndSession, ending }: SidebarFooterProps) {
  return (
    <div className="flex items-center gap-2.5 border-t border-rule px-4 py-3">
      <span
        aria-hidden="true"
        className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-signal-deep text-[0.6875rem] font-semibold text-white"
      >
        {initials(name)}
      </span>
      <span className="min-w-0 flex-1">
        <span className="block truncate text-[0.8125rem] font-medium text-ink">{name}</span>
        <span className="block truncate font-mono text-[0.6875rem] text-muted">{sessionId}</span>
      </span>
      <button
        type="button"
        onClick={onEndSession}
        disabled={ending}
        aria-label="End session"
        title="End session"
        className="inline-flex h-7 w-7 shrink-0 items-center justify-center rounded text-muted transition-colors hover:bg-danger-wash hover:text-danger disabled:cursor-not-allowed focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-signal"
      >
        {ending ? <Spinner className="text-muted" /> : <SignOutIcon />}
      </button>
    </div>
  );
}
