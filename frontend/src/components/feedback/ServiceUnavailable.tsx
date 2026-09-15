import { Button } from '@/components/ui';

interface ServiceUnavailableProps {
  message: string;
  onRetry: () => void;
  retrying: boolean;
}

/**
 * Shown when the API cannot be reached or cannot serve.
 *
 * Not the start screen: nothing is wrong with the session, and starting a new
 * one would fail the same way. The only useful action is to try again.
 */
export function ServiceUnavailable({ message, onRetry, retrying }: ServiceUnavailableProps) {
  return (
    <main className="flex min-h-dvh items-center justify-center bg-paper px-6">
      <div className="max-w-md text-center">
        <h1 className="text-title font-semibold text-ink">Can't reach the server</h1>
        <p className="mt-2 text-[0.9375rem] leading-relaxed text-slate">{message}</p>
        <Button onClick={onRetry} loading={retrying} className="mt-5">
          Try again
        </Button>
      </div>
    </main>
  );
}
