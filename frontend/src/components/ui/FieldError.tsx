interface FieldErrorProps {
  id: string;
  message?: string;
}

export function FieldError({ id, message }: FieldErrorProps) {
  if (!message) return null;

  return (
    <p id={id} className="mt-1 text-[0.75rem] leading-snug text-danger">
      {message}
    </p>
  );
}
