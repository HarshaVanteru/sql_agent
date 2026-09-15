import type { ConnectionDraft } from '@/types';

export interface SampleConnection {
  id: string;
  label: string;
  /** What is in it, so the buttons are a choice rather than a coin toss. */
  description: string;
  draft: ConnectionDraft;
}

/**
 * Databases to try the app against without having one of your own to hand.
 *
 * Both are public, read-only services published by the EMBL-EBI for exactly
 * this kind of use, so the credentials below are not secrets. Replace this list
 * with your own before a demo if you would rather show familiar data -- nothing
 * else imports these.
 */
export const SAMPLE_CONNECTIONS: readonly SampleConnection[] = [
  {
    id: 'rnacentral',
    label: 'RNAcentral',
    description: 'PostgreSQL · RNA sequences, ~100 tables',
    draft: {
      name: 'RNAcentral',
      dbType: 'postgresql',
      host: 'hh-pgsql-public.ebi.ac.uk',
      port: 5432,
      username: 'reader',
      password: 'NWDMCE5xdipIjRrp',
      databaseName: 'pfmegrnargs',
    },
  },
  {
    id: 'rfam',
    label: 'Rfam',
    description: 'MySQL · RNA families, no password needed',
    draft: {
      name: 'Rfam',
      dbType: 'mysql',
      host: 'mysql-rfam-public.ebi.ac.uk',
      port: 4497,
      username: 'rfamro',
      password: '',
      databaseName: 'Rfam',
    },
  },
];
