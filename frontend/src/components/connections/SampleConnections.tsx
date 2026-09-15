import { SampleConnectionButton } from './SampleConnectionButton';
import { SAMPLE_CONNECTIONS, type SampleConnection } from './sampleConnections';

interface SampleConnectionsProps {
  onPick: (sample: SampleConnection) => void;
  disabled: boolean;
}

export function SampleConnections({ onPick, disabled }: SampleConnectionsProps) {
  return (
    <div className="rounded border border-dashed border-rule bg-surface p-3">
      <p className="mb-2 text-[0.8125rem] text-slate">
        No database to hand? Fill the form with a public read-only one.
      </p>
      <div className="flex flex-col gap-2 sm:flex-row">
        {SAMPLE_CONNECTIONS.map((sample) => (
          <SampleConnectionButton
            key={sample.id}
            sample={sample}
            onPick={onPick}
            disabled={disabled}
          />
        ))}
      </div>
    </div>
  );
}
