import type { InputHTMLAttributes } from 'react';

import { FieldError } from './FieldError';
import { FieldLabel } from './FieldLabel';
import { controlClasses } from './fieldStyles';

interface TextFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  id: string;
  label: string;
  hint?: string;
  error?: string;
}

export function TextField({ id, label, hint, error, required, className, ...props }: TextFieldProps) {
  const errorId = `${id}-error`;
  const hintId = `${id}-hint`;
  // The error replaces the hint rather than stacking with it: two lines of small
  // text under one input is a wall, and the error is the urgent one.
  const describedBy = error ? errorId : hint ? hintId : undefined;

  return (
    <div className={className}>
      <FieldLabel htmlFor={id} required={required}>
        {label}
      </FieldLabel>
      <input
        {...props}
        id={id}
        required={required}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy}
        className={controlClasses(Boolean(error))}
      />
      <FieldError id={errorId} message={error} />
      {!error && hint && (
        <p id={hintId} className="mt-1 text-[0.75rem] leading-snug text-muted">
          {hint}
        </p>
      )}
    </div>
  );
}
