import { Link } from 'react-router-dom';

export function NotFoundPage() {
  return (
    <main className="flex min-h-dvh flex-col items-center justify-center gap-3 bg-paper px-6 text-center">
      <h1 className="text-title font-semibold text-ink">There's nothing at this address</h1>
      <p className="max-w-prose text-[0.9375rem] text-slate">
        The page you asked for does not exist.
      </p>
      <Link
        to="/"
        className="mt-2 text-[0.9375rem] font-medium text-signal underline-offset-4 hover:underline"
      >
        Start a session
      </Link>
    </main>
  );
}
