import { useState, type FormEvent } from 'react';

import { Button, FormError, TextField } from '@/components/ui';
import { errorMessage } from '@/lib/ApiError';

interface StartSessionFormProps {
  onStart: (name: string) => void;
  pending: boolean;
  error: unknown;
}

export function StartSessionForm({ onStart, pending, error }: StartSessionFormProps) {
  const [name, setName] = useState('');
  const trimmed = name.trim();

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (trimmed) onStart(trimmed);
  }

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-md">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
        <TextField
          id="session-name"
          label="Your name"
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder="Who's asking?"
          autoComplete="name"
          maxLength={100}
          autoFocus
          className="flex-1"
        />
        <Button type="submit" loading={pending} disabled={!trimmed} className="sm:w-36">
          Start session
        </Button>
      </div>
      {error != null && (
        <div className="mt-3">
          <FormError message={errorMessage(error, 'Could not start a session.')} />
        </div>
      )}
    </form>
  );
}
