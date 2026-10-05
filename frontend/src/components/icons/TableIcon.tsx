interface IconProps {
  className?: string;
}

export function TableIcon({ className = 'h-4 w-4' }: IconProps) {
  return (
    <svg
      viewBox="0 0 16 16"
      className={className}
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <rect x="2.5" y="3" width="11" height="10" rx="1" /><path d="M2.5 6.5h11M6.5 6.5V13" />
    </svg>
  );
}
