import { ClockIcon } from '@/components/icons/ClockIcon';
import type { TimeRemaining } from '@/hooks/useTimeRemaining';

interface SessionCountdownProps {
  time: TimeRemaining | null;
}

export function SessionCountdown({ time }: SessionCountdownProps) {
  if (!time) return null;

  return (
    <span className="inline-flex items-center gap-1.5 text-[0.8125rem] text-clock">
      <ClockIcon className="h-3.5 w-3.5" />
      {time.expired ? 'Session expired' : `${time.label} left`}
    </span>
  );
}
