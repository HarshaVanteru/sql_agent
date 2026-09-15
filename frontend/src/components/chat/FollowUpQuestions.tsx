import { SuggestedQuestions } from './SuggestedQuestions';

interface FollowUpQuestionsProps {
  questions: readonly string[];
  onPick: (question: string) => void;
  disabled: boolean;
}

/**
 * Three things worth asking next, sitting just above the composer.
 *
 * Drawn from what the last answer was about, so a conversation keeps its
 * thread instead of starting over at every turn -- and so someone who does not
 * know the database can keep going without having to invent the next question.
 */
export function FollowUpQuestions({ questions, onPick, disabled }: FollowUpQuestionsProps) {
  if (questions.length === 0) return null;

  return (
    <div>
      <p className="mb-1.5 text-xs text-slate">Ask next</p>
      <SuggestedQuestions
        questions={questions}
        onPick={onPick}
        disabled={disabled}
        align="start"
      />
    </div>
  );
}
