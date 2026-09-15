import { useEffect, useRef, type ReactNode } from 'react';

import { useMediaQuery } from '@/hooks/useMediaQuery';
import { cn } from '@/lib/cn';

interface AppSidebarProps {
  /** Only consulted below lg, where the sidebar is a drawer. */
  open: boolean;
  onClose: () => void;
  children: ReactNode;
}

/**
 * The databases and history panel: a column on a wide screen, a drawer on a
 * narrow one.
 *
 * One element either way rather than two rendered copies -- the same buttons
 * appearing twice in the DOM is two things for a screen reader to find and two
 * places for a bug to hide. Below lg it is taken out of flow and slid off to
 * the left; from lg it is a plain column again and `open` means nothing.
 */
export function AppSidebar({ open, onClose, children }: AppSidebarProps) {
  // From lg the panel is simply part of the page, so none of the drawer
  // bookkeeping applies -- and applying it anyway hid the whole navigation
  // from screen readers on every desktop.
  const isDrawer = !useMediaQuery('(min-width: 1024px)');
  const hidden = isDrawer && !open;

  const ref = useRef<HTMLElement>(null);
  useEffect(() => {
    // `inert` rather than aria-hidden alone: a panel slid off the left is
    // still in the tab order, and Tab would walk into controls nobody can see.
    if (ref.current) ref.current.toggleAttribute('inert', hidden);
  }, [hidden]);

  useEffect(() => {
    if (!open || !isDrawer) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [open, isDrawer, onClose]);

  return (
    <>
      {open && (
        <button
          type="button"
          aria-label="Close menu"
          onClick={onClose}
          className="fixed inset-0 z-30 bg-ink/30 lg:hidden"
        />
      )}
      <aside
        ref={ref}
        aria-hidden={hidden ? 'true' : undefined}
        className={cn(
          'flex w-72 shrink-0 flex-col divide-y divide-rule border-r border-rule bg-surface',
          'max-lg:fixed max-lg:inset-y-0 max-lg:left-0 max-lg:z-40 max-lg:w-[17rem]',
          'max-lg:shadow-[0_0_40px_-8px_rgba(16,28,43,0.35)]',
          'max-lg:transition-transform max-lg:duration-200 motion-reduce:max-lg:transition-none',
          open ? 'max-lg:translate-x-0' : 'max-lg:-translate-x-full max-lg:pointer-events-none',
          'lg:static lg:translate-x-0 lg:shadow-none lg:pointer-events-auto',
        )}
      >
        {children}
      </aside>
    </>
  );
}
