import { ShuffleIcon } from '@/components/icons/ShuffleIcon';

interface GenerateNameButtonProps {
  onGenerate: () => void;
  disabled: boolean;
}

/**
 * Fills the name field with a made-up handle.
 *
 * Inside the field rather than beside it: it acts on that one input, and the
 * row already ends with the button that actually starts the session. Two
 * buttons of equal weight side by side would be a question about which one to
 * press.
 */
export function GenerateNameButton({ onGenerate, disabled }: GenerateNameButtonProps) {
  return (
    <button
      type="button"
      onClick={onGenerate}
      disabled={disabled}
      title="Use a made-up name"
      className="inline-flex h-7 shrink-0 items-center gap-1.5 rounded px-2 text-xs font-medium text-slate transition-colors hover:bg-paper hover:text-ink disabled:opacity-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-signal"
    >
      <ShuffleIcon className="h-3.5 w-3.5" />
      Random
    </button>
  );
}
