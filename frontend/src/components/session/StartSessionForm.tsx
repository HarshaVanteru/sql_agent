import { useState, type FormEvent } from 'react';

import { Button, FormError, TextField } from '@/components/ui';
import { errorMessage, isApiError } from '@/lib/ApiError';
import { firstError, maxLength, required } from '@/lib/validation';

interface StartSessionFormProps {
  onStart: (name: string) => void;
  pending: boolean;
  error: unknown;
}

const RULES = [required('Name'), maxLength(100, 'Name')];

export function StartSessionForm({ onStart, pending, error }: StartSessionFormProps) {
  const [name, setName] = useState('');
  const [touched, setTouched] = useState(false);

  const validationError = firstError(name, RULES);
  const serverFieldError = isApiError(error) ? error.fields.name : undefined;
  const shown = (touched ? validationError : undefined) ?? serverFieldError;

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setTouched(true);
    if (!validationError) onStart(name.trim());
  }

  const formError =
    error != null && !serverFieldError ? errorMessage(error, 'Could not start a session.') : null;

  return (
    <form onSubmit={handleSubmit} noValidate className="w-full max-w-md">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start">
        <TextField
          id="session-name"
          label="Your name"
          required
          value={name}
          onChange={(event) => setName(event.target.value)}
          onBlur={() => setTouched(true)}
          error={shown}
          placeholder="Who's asking?"
          autoComplete="name"
          maxLength={100}
          autoFocus
          className="flex-1"
        />
        {/* Pushed past the label so it lines up with the input, not the label:
            text-xs is a 1rem line box plus the label's 0.25rem margin. */}
        <Button type="submit" loading={pending} className="sm:mt-5 sm:w-36">
          Start session
        </Button>
      </div>
      {formError && (
        <div className="mt-3">
          <FormError message={formError} />
        </div>
      )}
    </form>
  );
}
