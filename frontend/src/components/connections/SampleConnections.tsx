import { SampleConnectionButton } from './SampleConnectionButton';
import type { SampleConnection } from './sampleConnections';

interface SampleConnectionsProps {
  samples: readonly SampleConnection[];
  onPick: (sample: SampleConnection) => void;
  disabled: boolean;
}

/**
 * A hint above the form, not a menu.
 *
 * The label sits on its own line: three pills and a sentence on one row wraps
 * at this width, and a hint that reflows as the dialog opens reads as broken.
 */
export function SampleConnections({ samples, onPick, disabled }: SampleConnectionsProps) {
  if (samples.length === 0) return null;

  return (
    <div>
      <p className="mb-1.5 text-xs text-slate">No database to hand? Try one of these.</p>
      <div className="flex flex-wrap gap-1.5">
        {samples.map((sample) => (
          <SampleConnectionButton key={sample.id} sample={sample} onPick={onPick} disabled={disabled} />
        ))}
      </div>
    </div>
  );
}
