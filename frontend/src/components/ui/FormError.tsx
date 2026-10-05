import type { ErrorDebug } from '@/lib/ApiError';

interface FormErrorProps {
  /** Nothing renders when there is no error, so callers can pass through. */
  message?: string | null;
  /**
   * What actually broke, when the backend sent it. Folded away behind a
   * disclosure: the message above is the whole story for whoever is asking
   * questions, and this is for whoever has to go and fix the answer.
   */
  debug?: ErrorDebug;
}

/**
 * An error the person can act on. Stated plainly, in the interface's voice --
 * no apology, and never vague about what happened.
 */
export function FormError({ message, debug }: FormErrorProps) {
  if (!message) return null;

  const raw = [debug?.type, debug?.error].filter(Boolean).join(': ');
  const hasDetails = Boolean(debug?.hint || raw);

  return (
    <div
      role="alert"
      className="rounded border border-danger/25 bg-danger-wash px-3 py-2 text-sm text-danger"
    >
      <p>{message}</p>

      {hasDetails && (
        <details className="mt-1.5">
          <summary className="cursor-pointer select-none text-xs text-danger/70 hover:text-danger">
            Details
          </summary>
          {debug?.hint && <p className="mt-1.5 text-xs text-danger/80">{debug.hint}</p>}
          {raw && (
            <pre className="mt-1.5 max-h-40 overflow-auto whitespace-pre-wrap break-words font-mono text-[11px] leading-relaxed text-danger/70">
              {raw}
            </pre>
          )}
        </details>
      )}
    </div>
  );
}
