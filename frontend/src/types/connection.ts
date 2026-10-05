/** The database engines the agent can talk to. */
export const DATABASE_TYPES = ['postgresql', 'mysql'] as const;

export type DatabaseType = (typeof DATABASE_TYPES)[number];

export const DATABASE_LABELS: Record<DatabaseType, string> = {
  postgresql: 'PostgreSQL',
  mysql: 'MySQL',
};

export const DEFAULT_PORTS: Record<DatabaseType, number> = {
  postgresql: 5432,
  mysql: 3306,
};

export interface Connection {
  id: string;
  name: string;
  dbType: DatabaseType;
  createdAt: string;
}

/** What the person types into the connect form. */
export interface ConnectionDraft {
  name: string;
  dbType: DatabaseType;
  host: string;
  port: number;
  username: string;
  password: string;
  databaseName: string;
}
