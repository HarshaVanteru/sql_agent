import type { InputHTMLAttributes } from 'react';

import { cn } from '@/lib/cn';
import { FieldError } from './FieldError';
import { FieldLabel } from './FieldLabel';

interface TextFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  id: string;
  label: string;
  hint?: string;
  error?: string;
}

export function TextField({ id, label, hint, error, required, className, ...props }: TextFieldProps) {
  const errorId = `${id}-error`;
  const hintId = `${id}-hint`;
  // The error replaces the hint rather than stacking with it: two lines of
  // small text under one input is a wall, and the error is the urgent one.
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
        className={cn(
          'h-10 w-full rounded border bg-raised px-3 text-[0.9375rem] text-ink',
          'placeholder:text-muted',
          'focus:outline-none focus:ring-1',
          error
            ? 'border-danger focus:border-danger focus:ring-danger'
            : 'border-rule focus:border-signal focus:ring-signal',
          'disabled:bg-paper disabled:text-slate',
        )}
      />
      <FieldError id={errorId} message={error} />
      {!error && hint && (
        <p id={hintId} className="mt-1.5 text-[0.8125rem] leading-snug text-slate">
          {hint}
        </p>
      )}
    </div>
  );
}
