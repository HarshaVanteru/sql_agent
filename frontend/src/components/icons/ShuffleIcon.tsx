interface IconProps {
  className?: string;
}

export function ShuffleIcon({ className = 'h-4 w-4' }: IconProps) {
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
      <path d="M2.5 4h2.2l5.6 8h3.2M2.5 12h2.2l5.6-8h3.2" />
      <path d="M11.8 2.2L13.5 4l-1.7 1.8M11.8 10.2l1.7 1.8-1.7 1.8" />
    </svg>
  );
}
