import type { ReactNode } from 'react';

interface EmptyStateProps {
  title: string;
  /** What to do next. An empty screen is an invitation to act. */
  description?: string;
  action?: ReactNode;
}

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center px-6 py-12 text-center">
      <p className="text-[0.9375rem] font-medium text-ink">{title}</p>
      {description && <p className="mt-1.5 max-w-sm text-sm leading-relaxed text-slate">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
