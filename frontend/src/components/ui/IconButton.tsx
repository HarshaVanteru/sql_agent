import type { ButtonHTMLAttributes, ReactNode } from 'react';

import { cn } from '@/lib/cn';

interface IconButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** Required: the icon alone says nothing to a screen reader. */
  label: string;
  tone?: 'default' | 'danger';
  children: ReactNode;
}

export function IconButton({ label, tone = 'default', className, children, ...props }: IconButtonProps) {
  return (
    <button
      {...props}
      aria-label={label}
      title={label}
      className={cn(
        'inline-flex h-7 w-7 items-center justify-center rounded transition-colors duration-100',
        'focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-signal',
        tone === 'danger'
          ? 'text-muted hover:bg-danger-wash hover:text-danger'
          : 'text-muted hover:bg-paper hover:text-ink',
        className,
      )}
    >
      {children}
    </button>
  );
}
