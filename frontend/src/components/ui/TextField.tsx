import type { InputHTMLAttributes, ReactNode } from 'react';

import { FieldError } from './FieldError';
import { FieldLabel } from './FieldLabel';
import { controlClasses, controlGroupClasses, groupedInputClasses } from './fieldStyles';

interface TextFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  id: string;
  label: string;
  hint?: string;
  error?: string;
  /** An action that belongs to this field, drawn inside it on the right. */
  trailing?: ReactNode;
}

export function TextField({
  id,
  label,
  hint,
  error,
  trailing,
  required,
  className,
  ...props
}: TextFieldProps) {
  const errorId = `${id}-error`;
  const hintId = `${id}-hint`;
  // The error replaces the hint rather than stacking with it: two lines of small
  // text under one input is a wall, and the error is the urgent one.
  const describedBy = error ? errorId : hint ? hintId : undefined;

  const input = (
    <input
      {...props}
      id={id}
      required={required}
      aria-invalid={error ? true : undefined}
      aria-describedby={describedBy}
      className={trailing ? groupedInputClasses : controlClasses(Boolean(error))}
    />
  );

  return (
    <div className={className}>
      <FieldLabel htmlFor={id} required={required}>
        {label}
      </FieldLabel>
      {trailing ? (
        <div className={controlGroupClasses(Boolean(error))}>
          {input}
          {trailing}
        </div>
      ) : (
        input
      )}
      <FieldError id={errorId} message={error} />
      {!error && hint && (
        <p id={hintId} className="mt-1 text-[0.75rem] leading-snug text-muted">
          {hint}
        </p>
      )}
    </div>
  );
}
