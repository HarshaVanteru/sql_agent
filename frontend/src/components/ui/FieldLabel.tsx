import type { ReactNode } from 'react';

interface FieldLabelProps {
  htmlFor: string;
  children: ReactNode;
}

export function FieldLabel({ htmlFor, children }: FieldLabelProps) {
  return (
    <label htmlFor={htmlFor} className="mb-1.5 block text-sm font-medium text-ink">
      {children}
    </label>
  );
}
