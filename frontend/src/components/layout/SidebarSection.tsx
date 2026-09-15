import type { ReactNode } from 'react';

interface SidebarSectionProps {
  title: string;
  action?: ReactNode;
  children: ReactNode;
}

export function SidebarSection({ title, action, children }: SidebarSectionProps) {
  return (
    <section className="flex min-h-0 flex-col">
      <header className="flex items-center justify-between px-4 py-2.5">
        <h2 className="text-[0.8125rem] font-semibold text-ink">{title}</h2>
        {action}
      </header>
      <div className="min-h-0 flex-1 overflow-y-auto px-2 pb-2">{children}</div>
    </section>
  );
}
