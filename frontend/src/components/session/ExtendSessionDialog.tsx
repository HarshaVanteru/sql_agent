import { useEffect, useState } from 'react';

import { Button, FormError, Modal } from '@/components/ui';
import { useExtendSession } from '@/hooks/useExtendSession';
import { cn } from '@/lib/cn';
import { errorDebug, errorMessage } from '@/lib/ApiError';
import { EXTENSION_OPTIONS, projectExtension } from '@/lib/sessionExtension';
import type { ExtensionOption, Session } from '@/types';

interface ExtendSessionDialogProps {
  open: boolean;
  session: Session | null;
  onClose: () => void;
}

const formatEnd = (date: Date) =>
  date.toLocaleString([], {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });

/**
 * Add time to the session: 24 hours, 7 days or 30 days on top of what is left.
 *
 * Each option shows the exact moment the session would then end, so the choice
 * is made against a date rather than a duration -- and an option the 30-day
 * limit would cut short says so, instead of quietly delivering less.
 */
export function ExtendSessionDialog({ open, session, onClose }: ExtendSessionDialogProps) {
  const [choice, setChoice] = useState<ExtensionOption | null>(null);
  const extend = useExtendSession(onClose);

  // Options are re-projected each time the dialog opens, against the clock then.
  const projections = EXTENSION_OPTIONS.map((option) => ({
    ...option,
    ...(session ? projectExtension(session.expiresAt, option.ms) : null),
  }));

  useEffect(() => {
    if (!open) return;
    extend.reset();
    setChoice(projections.find((option) => !option.noGain)?.value ?? null);
    // Only on open: re-running on every render would undo the person's choice.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  const atMaximum = session ? projections.every((option) => option.noGain) : false;

  return (
    <Modal
      open={open}
      title="Extend session"
      description="Time is added to what the session has left. A session can never have more than 30 days left."
      onClose={onClose}
      footer={
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={onClose} disabled={extend.isPending}>
            Cancel
          </Button>
          <Button
            loading={extend.isPending}
            disabled={!choice || atMaximum}
            onClick={() => choice && extend.mutate(choice)}
          >
            Extend session
          </Button>
        </div>
      }
    >
      <fieldset className="space-y-2">
        <legend className="sr-only">How much time to add</legend>
        {projections.map((option) => {
          const disabled = Boolean(option.noGain) || extend.isPending;
          const selected = choice === option.value;
          return (
            <label
              key={option.value}
              className={cn(
                'flex cursor-pointer items-start gap-3 rounded-lg border px-3.5 py-3 transition-colors',
                'focus-within:outline focus-within:outline-2 focus-within:outline-offset-2 focus-within:outline-signal',
                selected ? 'border-signal bg-signal-faint' : 'border-rule bg-raised hover:border-muted',
                disabled && 'cursor-not-allowed opacity-50 hover:border-rule',
              )}
            >
              <input
                type="radio"
                name="extension"
                value={option.value}
                checked={selected}
                disabled={disabled}
                onChange={() => setChoice(option.value)}
                className="mt-1 h-4 w-4 shrink-0 accent-signal"
              />
              <span className="min-w-0">
                <span className="block text-[0.9375rem] font-medium text-ink">
                  Add {option.label}
                </span>
                <span className="block text-[0.8125rem] text-slate">
                  {option.noGain
                    ? 'Already at the 30-day limit'
                    : `Ends ${option.expiresAt ? formatEnd(option.expiresAt) : ''}`}
                  {option.clamped && !option.noGain && ' (limited to 30 days from now)'}
                </span>
              </span>
            </label>
          );
        })}

        <div className="pt-1">
          <FormError
            message={extend.error ? errorMessage(extend.error, 'The session could not be extended.') : null}
            debug={errorDebug(extend.error)}
          />
        </div>
      </fieldset>
    </Modal>
  );
}
