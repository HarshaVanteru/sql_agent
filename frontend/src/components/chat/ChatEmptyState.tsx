import { SuggestedQuestions } from './SuggestedQuestions';

interface ChatEmptyStateProps {
  connectionName: string;
  onPick: (question: string) => void;
  disabled: boolean;
}

export function ChatEmptyState({ connectionName, onPick, disabled }: ChatEmptyStateProps) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-5 px-4 py-10 text-center">
      <div className="max-w-md">
        <p className="text-title font-semibold text-ink">Ask {connectionName} something</p>
        <p className="mt-2 text-[0.9375rem] leading-relaxed text-slate">
          The agent reads the schema itself, writes the SQL, and shows you both the query and the
          rows it came back with.
        </p>
      </div>
      <SuggestedQuestions onPick={onPick} disabled={disabled} />
    </div>
  );
}
