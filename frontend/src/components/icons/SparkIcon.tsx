interface IconProps {
  className?: string;
}

/** The mark on a suggested question: something the agent thought of, not you. */
export function SparkIcon({ className = 'h-3.5 w-3.5' }: IconProps) {
  return (
    <svg viewBox="0 0 16 16" className={className} fill="currentColor" aria-hidden="true">
      <path d="M8 1.5c.28 2.4 1.6 3.72 4 4-2.4.28-3.72 1.6-4 4-.28-2.4-1.6-3.72-4-4 2.4-.28 3.72-1.6 4-4Z" />
      <path d="M12.75 9.5c.16 1.3.88 2.02 2.18 2.18-1.3.16-2.02.88-2.18 2.18-.16-1.3-.88-2.02-2.18-2.18 1.3-.16 2.02-.88 2.18-2.18Z" />
    </svg>
  );
}
