import { SelectField } from '@/components/ui';
import { DATABASE_LABELS, DATABASE_TYPES, type DatabaseType } from '@/types';

const OPTIONS = DATABASE_TYPES.map((value) => ({ value, label: DATABASE_LABELS[value] }));

interface DatabaseTypeFieldProps {
  value: DatabaseType;
  onChange: (dbType: DatabaseType) => void;
  error?: string;
  disabled?: boolean;
}

export function DatabaseTypeField({ value, onChange, error, disabled }: DatabaseTypeFieldProps) {
  return (
    <SelectField
      id="connection-db-type"
      label="Engine"
      required
      options={OPTIONS}
      value={value}
      error={error}
      disabled={disabled}
      onChange={(event) => onChange(event.target.value as DatabaseType)}
    />
  );
}
