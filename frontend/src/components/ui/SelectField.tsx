import type { SelectHTMLAttributes } from 'react';

import { cn } from '@/lib/cn';
import { FieldError } from './FieldError';
import { FieldLabel } from './FieldLabel';

interface Option {
  value: string;
  label: string;
}

interface SelectFieldProps extends SelectHTMLAttributes<HTMLSelectElement> {
  id: string;
  label: string;
  options: readonly Option[];
  error?: string;
}

export function SelectField({
  id,
  label,
  options,
  error,
  required,
  className,
  ...props
}: SelectFieldProps) {
  const errorId = `${id}-error`;

  return (
    <div className={className}>
      <FieldLabel htmlFor={id} required={required}>
        {label}
      </FieldLabel>
      <select
        {...props}
        id={id}
        required={required}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? errorId : undefined}
        className={cn(
          'h-10 w-full rounded border bg-raised px-3 text-[0.9375rem] text-ink',
          'focus:outline-none focus:ring-1',
          error
            ? 'border-danger focus:border-danger focus:ring-danger'
            : 'border-rule focus:border-signal focus:ring-signal',
        )}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      <FieldError id={errorId} message={error} />
    </div>
  );
}
