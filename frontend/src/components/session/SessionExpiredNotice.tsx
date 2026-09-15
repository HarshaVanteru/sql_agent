interface SessionExpiredNoticeProps {
  show: boolean;
}

/**
 * Shown on the way back from a session that ran out. States what happened and
 * what to do, in the interface's voice -- no apology, nothing vague.
 */
export function SessionExpiredNotice({ show }: SessionExpiredNoticeProps) {
  if (!show) return null;

  return (
    <p
      role="status"
      className="mb-6 max-w-prose rounded border border-clock/30 bg-clock-wash px-3 py-2 text-[0.9375rem] text-ink"
    >
      That session has ended, and the databases connected to it are gone. Start another to pick
      things back up.
    </p>
  );
}
