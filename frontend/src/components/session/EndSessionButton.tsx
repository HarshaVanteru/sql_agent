import { useState } from 'react';

import { Button } from '@/components/ui';

interface EndSessionButtonProps {
  onConfirm: () => void;
  pending: boolean;
}

/**
 * Ending a session deletes every connected database and every conversation, so
 * it asks first -- inline, since a dialog for a two-word question is heavier
 * than the question.
 */
export function EndSessionButton({ onConfirm, pending }: EndSessionButtonProps) {
  const [confirming, setConfirming] = useState(false);

  if (!confirming) {
    return (
      <Button variant="ghost" size="sm" onClick={() => setConfirming(true)}>
        End session
      </Button>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <span className="hidden text-[0.8125rem] text-slate sm:inline">Delete everything?</span>
      <Button variant="danger" size="sm" loading={pending} onClick={onConfirm}>
        End session
      </Button>
      <Button variant="ghost" size="sm" onClick={() => setConfirming(false)} disabled={pending}>
        Keep
      </Button>
    </div>
  );
}
