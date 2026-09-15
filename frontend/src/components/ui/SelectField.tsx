import type { SelectHTMLAttributes } from 'react';

import { cn } from '@/lib/cn';
import { FieldLabel } from './FieldLabel';

interface Option {
  value: string;
  label: string;
}

interface SelectFieldProps extends SelectHTMLAttributes<HTMLSelectElement> {
  id: string;
  label: string;
  options: readonly Option[];
}

export function SelectField({ id, label, options, className, ...props }: SelectFieldProps) {
  return (
    <div className={className}>
      <FieldLabel htmlFor={id}>{label}</FieldLabel>
      <select
        {...props}
        id={id}
        className={cn(
          'h-10 w-full rounded border border-rule bg-raised px-3 text-[0.9375rem] text-ink',
          'focus:border-signal focus:outline-none focus:ring-1 focus:ring-signal',
        )}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}
