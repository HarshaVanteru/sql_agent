import type { SelectHTMLAttributes } from 'react';

import { ChevronDownIcon } from '@/components/icons/ChevronDownIcon';
import { FieldError } from './FieldError';
import { FieldLabel } from './FieldLabel';
import { controlClasses } from './fieldStyles';

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
      {/* appearance-none and our own chevron: the platform arrow is a different
          shape and weight in every browser, and sits next to our own icons. */}
      <div className="relative">
        <select
          {...props}
          id={id}
          required={required}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? errorId : undefined}
          className={controlClasses(Boolean(error), 'appearance-none pr-8')}
        >
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <ChevronDownIcon className="pointer-events-none absolute right-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
      </div>
      <FieldError id={errorId} message={error} />
    </div>
  );
}
