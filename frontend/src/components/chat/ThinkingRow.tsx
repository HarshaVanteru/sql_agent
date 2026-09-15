/**
 * Shown while the agent works. It explores the schema over several model calls,
 * so this can run for a few seconds and saying what it is doing beats a bare
 * spinner.
 */
export function ThinkingRow() {
  return (
    <div className="flex items-center gap-2.5 text-[0.9375rem] text-slate">
      <span className="flex gap-1" aria-hidden="true">
        {[0, 150, 300].map((delay) => (
          <span
            key={delay}
            className="h-1.5 w-1.5 animate-pulse rounded-full bg-muted motion-reduce:animate-none"
            style={{ animationDelay: `${delay}ms` }}
          />
        ))}
      </span>
      Reading the schema and writing a query
    </div>
  );
}
