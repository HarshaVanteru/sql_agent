import { SelectField } from '@/components/ui';
import { DATABASE_LABELS, DATABASE_TYPES, type DatabaseType } from '@/types';

const OPTIONS = DATABASE_TYPES.map((value) => ({ value, label: DATABASE_LABELS[value] }));

interface DatabaseTypeFieldProps {
  value: DatabaseType;
  onChange: (dbType: DatabaseType) => void;
  disabled?: boolean;
}

export function DatabaseTypeField({ value, onChange, disabled }: DatabaseTypeFieldProps) {
  return (
    <SelectField
      id="connection-db-type"
      label="Engine"
      options={OPTIONS}
      value={value}
      disabled={disabled}
      onChange={(event) => onChange(event.target.value as DatabaseType)}
    />
  );
}
