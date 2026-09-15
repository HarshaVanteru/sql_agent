import { useEffect, useRef, type ReactNode } from 'react';

import { CloseIcon } from '@/components/icons/CloseIcon';
import { IconButton } from './IconButton';

interface ModalProps {
  open: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
}

export function Modal({ open, title, onClose, children }: ModalProps) {
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
      className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-ink/25 p-4 sm:items-center"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="my-auto w-full max-w-md rounded-md border border-rule bg-raised"
      >
        <header className="flex items-center justify-between border-b border-rule px-5 py-3.5">
          <h2 className="text-[0.9375rem] font-semibold text-ink">{title}</h2>
          <IconButton label="Close" onClick={onClose}>
            <CloseIcon />
          </IconButton>
        </header>
        <div className="p-5">{children}</div>
      </div>
    </div>
  );
}
