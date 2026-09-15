const SUGGESTIONS = [
  'What tables are in here?',
  'Show me 10 rows from the largest table',
  'How many records were created this month?',
];

interface SuggestedQuestionsProps {
  onPick: (question: string) => void;
  disabled: boolean;
}

export function SuggestedQuestions({ onPick, disabled }: SuggestedQuestionsProps) {
  return (
    <ul className="flex flex-wrap justify-center gap-2">
      {SUGGESTIONS.map((question) => (
        <li key={question}>
          <button
            type="button"
            disabled={disabled}
            onClick={() => onPick(question)}
            className="rounded-full border border-rule bg-raised px-3 py-1.5 text-[0.8125rem] text-slate transition-colors hover:border-ink hover:text-ink disabled:opacity-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-signal"
          >
            {question}
          </button>
        </li>
      ))}
    </ul>
  );
}
