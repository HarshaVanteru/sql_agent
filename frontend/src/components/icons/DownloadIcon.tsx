interface IconProps {
  className?: string;
}

export function DownloadIcon({ className = 'h-4 w-4' }: IconProps) {
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
      <path d="M8 2v8M5 7.5 8 10.5l3-3M2.5 13h11" />
    </svg>
  );
}
