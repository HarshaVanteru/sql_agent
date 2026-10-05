interface IconProps {
  className?: string;
}

export function SlidersIcon({ className = 'h-4 w-4' }: IconProps) {
  return (
    <svg
      viewBox="0 0 16 16"
      className={className}
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      aria-hidden="true"
    >
      <path d="M2 4.5h4M9.5 4.5H14M2 11.5h5.5M11 11.5H14" />
      <circle cx="7.75" cy="4.5" r="1.75" />
      <circle cx="9.25" cy="11.5" r="1.75" />
    </svg>
  );
}
