import { useEffect } from 'react';

import { PlusIcon } from '@/components/icons/PlusIcon';
import { cn } from '@/lib/cn';

interface NewQueryButtonProps {
  onClick: () => void;
  disabled: boolean;
}

/** Mac says ⌘K, everything else says Ctrl K. */
const isMac = typeof navigator !== 'undefined' && /Mac|iPhone|iPad/.test(navigator.platform);

export function NewQueryButton({ onClick, disabled }: NewQueryButtonProps) {
  // The shortcut is advertised on the button, so it has to actually work --
  // a chip showing a key combination that does nothing is worse than no chip.
  useEffect(() => {
    if (disabled) return;
    function onKeyDown(event: KeyboardEvent) {
      if (event.key.toLowerCase() !== 'k') return;
      if (!(isMac ? event.metaKey : event.ctrlKey)) return;
      event.preventDefault();
      onClick();
    }
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [onClick, disabled]);

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={cn(
        'flex w-full items-center gap-2 rounded-lg border border-rule bg-raised px-3 py-2.5 text-left',
        'transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-signal',
        disabled ? 'cursor-not-allowed opacity-50' : 'hover:border-signal/40 hover:bg-signal-faint',
      )}
    >
      <PlusIcon className="h-4 w-4 shrink-0 text-signal" />
      <span className="flex-1 text-sm font-medium text-ink">New query</span>
      <kbd className="shrink-0 rounded border border-rule bg-surface px-1.5 py-0.5 font-sans text-[0.6875rem] text-muted">
        {isMac ? '⌘K' : 'Ctrl K'}
      </kbd>
    </button>
  );
}
