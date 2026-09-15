import { SampleConnectionButton } from './SampleConnectionButton';
import { SAMPLE_CONNECTIONS, type SampleConnection } from './sampleConnections';

interface SampleConnectionsProps {
  onPick: (sample: SampleConnection) => void;
  disabled: boolean;
}

/**
 * One line, not a panel of cards.
 *
 * These are a shortcut for someone who has no database to hand -- useful, but
 * not the point of the dialog, and the cards they used to sit in pushed the
 * actual form off the bottom of the screen.
 */
export function SampleConnections({ onPick, disabled }: SampleConnectionsProps) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="text-xs text-slate">No database to hand?</span>
      {SAMPLE_CONNECTIONS.map((sample) => (
        <SampleConnectionButton key={sample.id} sample={sample} onPick={onPick} disabled={disabled} />
      ))}
    </div>
  );
}
