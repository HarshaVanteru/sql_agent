import { useEffect, useRef, type ReactNode } from 'react';

import { CloseIcon } from '@/components/icons/CloseIcon';
import { IconButton } from './IconButton';

interface ModalProps {
  open: boolean;
  title: string;
  /** One line under the title, when the dialog needs framing. */
  description?: string;
  /** Pinned below the scrolling body, so actions stay reachable. */
  footer?: ReactNode;
  onClose: () => void;
  children: ReactNode;
}

export function Modal({ open, title, description, footer, onClose, children }: ModalProps) {
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKeyDown);

    // Move focus in, so a keyboard reader is not left behind the overlay.
    panelRef.current?.querySelector<HTMLElement>('input, select, button')?.focus();

    const { overflow } = document.body.style;
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKeyDown);
      document.body.style.overflow = overflow;
    };
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-ink/30 p-0 backdrop-blur-[2px] sm:items-center sm:p-4"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      {/*
        A column capped at the viewport, with only the middle scrolling. However
        tall the contents get, the dialog stays inside the window and the footer
        stays in reach -- which is not true of a panel that simply grows.
        Elevation is the one shadow in the app: it is what separates the dialog
        from the page, not decoration.
      */}
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="flex max-h-[92dvh] w-full max-w-lg flex-col overflow-hidden rounded-t-xl border border-rule bg-raised shadow-[0_16px_48px_-12px_rgba(16,28,43,0.28)] sm:max-h-[86dvh] sm:rounded-xl"
      >
        <header className="flex shrink-0 items-start justify-between gap-4 px-5 pb-3 pt-4">
          <div className="min-w-0">
            <h2 className="text-[0.9375rem] font-semibold tracking-tight text-ink">{title}</h2>
            {description && <p className="mt-0.5 text-[0.8125rem] text-slate">{description}</p>}
          </div>
          <IconButton label="Close" onClick={onClose} className="-mr-1 shrink-0">
            <CloseIcon />
          </IconButton>
        </header>

        <div className="min-h-0 flex-1 overflow-y-auto px-5 pb-4">{children}</div>

        {footer && (
          <footer className="shrink-0 border-t border-rule bg-surface px-5 py-3">{footer}</footer>
        )}
      </div>
    </div>
  );
}
