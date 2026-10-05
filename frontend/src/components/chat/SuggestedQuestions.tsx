import { SparkIcon } from '@/components/icons/SparkIcon';

interface SuggestedQuestionsProps {
  questions: readonly string[];
  onPick: (question: string) => void;
  disabled: boolean;
  /** Centred under the empty state, left-aligned above the composer. */
  align?: 'center' | 'start';
}

export function SuggestedQuestions({
  questions,
  onPick,
  disabled,
  align = 'center',
}: SuggestedQuestionsProps) {
  if (questions.length === 0) return null;

  return (
    <ul className={`flex flex-wrap gap-2 ${align === 'center' ? 'justify-center' : ''}`}>
      {questions.map((question) => (
        <li key={question}>
          <button
            type="button"
            disabled={disabled}
            onClick={() => onPick(question)}
            className="flex items-center gap-2 rounded-full border border-rule bg-raised px-3 py-1.5 text-left text-[0.8125rem] text-slate transition-colors hover:border-signal/40 hover:bg-signal-faint hover:text-ink disabled:opacity-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-signal"
          >
            {/* The mark says where the question came from: the agent proposed
                it from the last answer, you did not type it. */}
            <SparkIcon className="h-3 w-3 shrink-0 text-signal-bright" />
            {question}
          </button>
        </li>
      ))}
    </ul>
  );
}
