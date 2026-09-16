/**
 * Shown while the agent works. It explores the schema over several model calls,
 * so this can run for a few seconds and saying what it is doing beats a bare
 * spinner.
 *
 * Built to the same shape as a finished answer -- same avatar, same name in the
 * same place -- so when the real turn arrives it replaces this one without the
 * column jumping.
 */
export function ThinkingRow() {
  return (
    <div className="flex w-full min-w-0 flex-col items-start gap-3">
      <div className="flex items-center gap-2.5">
        <span
          aria-hidden="true"
          className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-signal-bright font-serif text-[0.8125rem] font-semibold text-white"
        >
          A
        </span>
        <h3 className="font-serif text-[0.9375rem] italic text-ink">Database copilot</h3>
      </div>

      <p className="flex items-center gap-2.5 rounded-xl border border-rule bg-raised px-4 py-3 text-[0.9375rem] text-slate">
        <span className="flex gap-1" aria-hidden="true">
          {[0, 150, 300].map((delay) => (
            <span
              key={delay}
              className="h-1.5 w-1.5 animate-pulse rounded-full bg-signal-bright motion-reduce:animate-none"
              style={{ animationDelay: `${delay}ms` }}
            />
          ))}
        </span>
        Reading the schema and writing a query
      </p>
    </div>
  );
}
