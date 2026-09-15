import { MenuIcon } from '@/components/icons/MenuIcon';
import { EndSessionButton } from '@/components/session/EndSessionButton';
import { SessionCountdown } from '@/components/session/SessionCountdown';
import { IconButton } from '@/components/ui';
import type { TimeRemaining } from '@/hooks/useTimeRemaining';

interface AppHeaderProps {
  name: string;
  time: TimeRemaining | null;
  onOpenMenu: () => void;
  onEndSession: () => void;
  endingSession: boolean;
}

export function AppHeader({
  name,
  time,
  onOpenMenu,
  onEndSession,
  endingSession,
}: AppHeaderProps) {
  return (
    <header className="flex h-14 shrink-0 items-center justify-between gap-2 border-b border-rule bg-raised px-3 sm:gap-4 sm:px-4">
      <div className="flex min-w-0 items-center gap-2 sm:gap-3">
        <div className="lg:hidden">
          <IconButton label="Open menu" onClick={onOpenMenu}>
            <MenuIcon />
          </IconButton>
        </div>
        {/* The product name is the least useful thing here once someone is
            inside it, so it is the first to go when the row gets tight. */}
        <span className="hidden shrink-0 font-semibold tracking-tight text-ink sm:inline">
          Ask your database
        </span>
        <span className="min-w-0 truncate text-sm text-slate">{name}</span>
      </div>
      <div className="flex shrink-0 items-center gap-2 sm:gap-4">
        <SessionCountdown time={time} />
        <EndSessionButton onConfirm={onEndSession} pending={endingSession} />
      </div>
    </header>
  );
}
