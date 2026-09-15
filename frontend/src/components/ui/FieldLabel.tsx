import type { ReactNode } from 'react';

import { RequiredMark } from './RequiredMark';

interface FieldLabelProps {
  htmlFor: string;
  required?: boolean;
  children: ReactNode;
}

export function FieldLabel({ htmlFor, required = false, children }: FieldLabelProps) {
  return (
    <label htmlFor={htmlFor} className="mb-1.5 block text-sm font-medium text-ink">
      {children}
      {required && <RequiredMark />}
    </label>
  );
}
