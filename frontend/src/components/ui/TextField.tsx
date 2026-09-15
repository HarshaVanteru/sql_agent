import type { InputHTMLAttributes } from 'react';

import { cn } from '@/lib/cn';
import { FieldLabel } from './FieldLabel';

interface TextFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  id: string;
  label: string;
  hint?: string;
}

export function TextField({ id, label, hint, className, ...props }: TextFieldProps) {
  const hintId = hint ? `${id}-hint` : undefined;

  return (
    <div className={className}>
      <FieldLabel htmlFor={id}>{label}</FieldLabel>
      <input
        {...props}
        id={id}
        aria-describedby={hintId}
        className={cn(
          'h-10 w-full rounded border border-rule bg-raised px-3 text-[0.9375rem] text-ink',
          'placeholder:text-muted',
          'focus:border-signal focus:outline-none focus:ring-1 focus:ring-signal',
          'disabled:bg-paper disabled:text-slate',
        )}
      />
      {hint && (
        <p id={hintId} className="mt-1.5 text-[0.8125rem] leading-snug text-slate">
          {hint}
        </p>
      )}
    </div>
  );
}
