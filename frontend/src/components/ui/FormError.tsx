interface FormErrorProps {
  /** Nothing renders when there is no error, so callers can pass through. */
  message?: string | null;
}

/**
 * An error the person can act on. Stated plainly, in the interface's voice --
 * no apology, and never vague about what happened.
 */
export function FormError({ message }: FormErrorProps) {
  if (!message) return null;

  return (
    <p role="alert" className="rounded border border-danger/25 bg-danger-wash px-3 py-2 text-sm text-danger">
      {message}
    </p>
  );
}
