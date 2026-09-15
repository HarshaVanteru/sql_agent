import { SessionCountdown } from '@/components/session/SessionCountdown';
import { EndSessionButton } from '@/components/session/EndSessionButton';
import type { TimeRemaining } from '@/hooks/useTimeRemaining';

interface AppHeaderProps {
  name: string;
  time: TimeRemaining | null;
  onEndSession: () => void;
  endingSession: boolean;
}

export function AppHeader({ name, time, onEndSession, endingSession }: AppHeaderProps) {
  return (
    <header className="flex h-14 shrink-0 items-center justify-between gap-4 border-b border-rule bg-raised px-4">
      <div className="flex min-w-0 items-baseline gap-3">
        <span className="shrink-0 font-semibold tracking-tight text-ink">Ask your database</span>
        <span className="truncate text-sm text-slate">{name}</span>
      </div>
      <div className="flex shrink-0 items-center gap-4">
        <SessionCountdown time={time} />
        <EndSessionButton onConfirm={onEndSession} pending={endingSession} />
      </div>
    </header>
  );
}
