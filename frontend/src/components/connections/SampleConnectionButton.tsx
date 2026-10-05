import { DatabaseIcon } from '@/components/icons/DatabaseIcon';
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
      className="group inline-flex h-8 items-center gap-1.5 rounded-full border border-rule bg-raised pl-2.5 pr-3 text-sm transition-colors hover:border-signal hover:bg-signal-wash disabled:opacity-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-signal"
    >
      <DatabaseIcon className="h-3.5 w-3.5 text-muted group-hover:text-signal" />
      <span className="font-medium text-ink">{sample.label}</span>
      <span className="text-xs text-muted">{sample.engine}</span>
    </button>
  );
}
