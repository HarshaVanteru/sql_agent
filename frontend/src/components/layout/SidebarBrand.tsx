import { SlidersIcon } from '@/components/icons/SlidersIcon';
import { IconButton } from '@/components/ui';

interface SidebarBrandProps {
  onOpenSettings?: () => void;
}

/**
 * The wordmark, at the top of the sidebar.
 *
 * The mark is the product's initial cut out of a filled square rather than a
 * drawn logo: it survives being 32px, it needs no asset, and it is the one
 * place the forest green appears at full strength.
 */
export function SidebarBrand({ onOpenSettings }: SidebarBrandProps) {
  return (
    <div className="flex items-center gap-3 px-4 pb-3 pt-4">
      <span
        aria-hidden="true"
        className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-signal font-serif text-lg font-semibold leading-none text-white"
      >
        A
      </span>
      <span className="min-w-0 flex-1">
        <span className="block font-serif text-base font-semibold leading-tight text-ink">
          Ask your database
        </span>
        <span className="block truncate text-[0.6875rem] tracking-[0.14em] text-muted">
          AI WORKSPACE
        </span>
      </span>
      {onOpenSettings && (
        <IconButton label="Workspace settings" onClick={onOpenSettings}>
          <SlidersIcon />
        </IconButton>
      )}
    </div>
  );
}
