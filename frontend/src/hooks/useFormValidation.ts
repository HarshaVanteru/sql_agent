import { useCallback, useMemo, useState } from 'react';

import { firstError, type Rule } from '@/lib/validation';

export type RuleMap<V> = { [K in keyof V]?: Array<Rule<V[K]>> };
export type ErrorMap<V> = Partial<Record<keyof V, string>>;

interface UseFormValidation<V> {
  /** The message to show for a field: its own, or one the server sent back. */
  errorFor: (field: keyof V) => string | undefined;
  /** True once every rule passes. Drives whether submit is enabled. */
  valid: boolean;
  /** Mark a field as touched, so its error can start showing. */
  touch: (field: keyof V) => void;
  /** Touch everything and report whether it is safe to submit. */
  touchAllAndCheck: () => boolean;
  /** Attach per-field messages the server returned. */
  setServerErrors: (errors: ErrorMap<V>) => void;
  /** Forget a field's server message once it is edited. */
  clearServerError: (field: keyof V) => void;
}

/**
 * Validation that stays quiet until someone has had a go at a field.
 *
 * Errors appear on blur or on submit, never while a field is still being typed
 * into for the first time -- telling someone their host is invalid after one
 * character is noise, not help.
 */
export function useFormValidation<V extends object>(
  values: V,
  rules: RuleMap<V>,
): UseFormValidation<V> {
  const [touched, setTouched] = useState<Partial<Record<keyof V, boolean>>>({});
  const [serverErrors, setServerErrorState] = useState<ErrorMap<V>>({});

  const errors = useMemo(() => {
    const found: ErrorMap<V> = {};
    for (const key of Object.keys(rules) as Array<keyof V>) {
      const fieldRules = rules[key];
      if (!fieldRules) continue;
      const message = firstError(values[key], fieldRules as Array<Rule<V[keyof V]>>);
      if (message) found[key] = message;
    }
    return found;
  }, [values, rules]);

  const valid = Object.keys(errors).length === 0;

  const errorFor = useCallback(
    (field: keyof V) => (touched[field] ? errors[field] : undefined) ?? serverErrors[field],
    [touched, errors, serverErrors],
  );

  const touch = useCallback((field: keyof V) => {
    setTouched((current) => ({ ...current, [field]: true }));
  }, []);

  const touchAllAndCheck = useCallback(() => {
    setTouched(
      Object.fromEntries(Object.keys(rules).map((key) => [key, true])) as Partial<
        Record<keyof V, boolean>
      >,
    );
    return Object.keys(errors).length === 0;
  }, [rules, errors]);

  const setServerErrors = useCallback((next: ErrorMap<V>) => setServerErrorState(next), []);

  const clearServerError = useCallback((field: keyof V) => {
    setServerErrorState((current) => {
      if (!(field in current)) return current;
      const next = { ...current };
      delete next[field];
      return next;
    });
  }, []);

  return { errorFor, valid, touch, touchAllAndCheck, setServerErrors, clearServerError };
}
