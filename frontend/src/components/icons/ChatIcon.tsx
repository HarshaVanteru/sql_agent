interface IconProps {
  className?: string;
}

export function ChatIcon({ className = 'h-4 w-4' }: IconProps) {
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
      <path d="M13.5 8.5c0 2.5-2.5 4.5-5.5 4.5a6.9 6.9 0 0 1-1.9-.26L3 13.5l.9-2.4A4.3 4.3 0 0 1 2.5 8.5C2.5 6 5 4 8 4s5.5 2 5.5 4.5Z" />
    </svg>
  );
}
