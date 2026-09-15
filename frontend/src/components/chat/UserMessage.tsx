interface UserMessageProps {
  content: string;
}

export function UserMessage({ content }: UserMessageProps) {
  return (
    <div className="flex w-full min-w-0 justify-end">
      <p className="max-w-prose whitespace-pre-wrap break-words rounded-md bg-signal px-3.5 py-2 text-[0.9375rem] leading-relaxed text-white">
        {content}
      </p>
    </div>
  );
}
