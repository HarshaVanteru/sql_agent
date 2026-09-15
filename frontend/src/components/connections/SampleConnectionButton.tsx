import type { SampleConnection } from './sampleConnections';

interface SampleConnectionButtonProps {
  sample: SampleConnection;
  onPick: (sample: SampleConnection) => void;
  disabled: boolean;
}

export function SampleConnectionButton({ sample, onPick, disabled }: SampleConnectionButtonProps) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={() => onPick(sample)}
      className="flex-1 rounded border border-rule bg-raised px-3 py-2 text-left transition-colors hover:border-ink disabled:opacity-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-signal"
    >
      <span className="block text-sm font-medium text-ink">{sample.label}</span>
      <span className="block text-xs text-slate">{sample.description}</span>
    </button>
  );
}
