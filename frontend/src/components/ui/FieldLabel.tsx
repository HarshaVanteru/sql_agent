import type { ReactNode } from 'react';

import { RequiredMark } from './RequiredMark';

interface FieldLabelProps {
  htmlFor: string;
  required?: boolean;
  children: ReactNode;
}

export function FieldLabel({ htmlFor, required = false, children }: FieldLabelProps) {
  return (
    <label
      htmlFor={htmlFor}
      className="mb-1 block text-xs font-medium tracking-[0.01em] text-slate"
    >
      {children}
      {required && <RequiredMark />}
    </label>
  );
}
