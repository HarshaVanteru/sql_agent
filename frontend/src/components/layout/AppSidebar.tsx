import type { ReactNode } from 'react';

interface AppSidebarProps {
  children: ReactNode;
}

export function AppSidebar({ children }: AppSidebarProps) {
  return (
    <aside className="flex w-72 shrink-0 flex-col divide-y divide-rule border-r border-rule bg-surface max-lg:hidden">
      {children}
    </aside>
  );
}
