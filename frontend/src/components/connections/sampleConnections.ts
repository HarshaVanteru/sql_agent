import type { ConnectionDraft } from '@/types';

export interface SampleConnection {
  id: string;
  label: string;
  /** The engine, shown beside the name so the pair is a choice not a coin toss. */
  engine: string;
  draft: ConnectionDraft;
}

/**
 * Databases to try the app against without having one of your own to hand.
 *
 * All public, read-only services published by the EMBL-EBI and the UCSC Genome
 * Browser for exactly this kind of use, so the credentials below are not
 * secrets. Every one was connected to before being added.
 *
 * Chosen for size as much as subject: UCSC also publishes hg19 and hg38, and
 * those have twelve thousand and three thousand tables. `list_tables` hands its
 * answer to the model, so a database like that spends the context window on a
 * table listing before the question is even considered. Nothing here is much
 * past a hundred.
 *
 * Replace this list with your own before a demo if you would rather show
 * familiar data -- nothing else imports these.
 */
export const SAMPLE_CONNECTIONS: readonly SampleConnection[] = [
  {
    id: 'rnacentral',
    label: 'RNAcentral',
    engine: 'PostgreSQL',
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
    engine: 'MySQL',
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
  {
    id: 'gene-ontology',
    label: 'Gene Ontology',
    engine: 'MySQL',
    draft: {
      name: 'Gene Ontology',
      dbType: 'mysql',
      host: 'genome-mysql.soe.ucsc.edu',
      port: 3306,
      username: 'genome',
      password: '',
      databaseName: 'go',
    },
  },
  {
    id: 'uniprot',
    label: 'UniProt',
    engine: 'MySQL',
    draft: {
      name: 'UniProt',
      dbType: 'mysql',
      host: 'genome-mysql.soe.ucsc.edu',
      port: 3306,
      username: 'genome',
      password: '',
      databaseName: 'uniProt',
    },
  },
  {
    id: 'proteome',
    label: 'Proteome',
    engine: 'MySQL',
    draft: {
      name: 'Proteome',
      dbType: 'mysql',
      host: 'genome-mysql.soe.ucsc.edu',
      port: 3306,
      username: 'genome',
      password: '',
      databaseName: 'proteome',
    },
  },
  {
    id: 'visigene',
    label: 'VisiGene',
    engine: 'MySQL',
    draft: {
      name: 'VisiGene',
      dbType: 'mysql',
      host: 'genome-mysql.soe.ucsc.edu',
      port: 3306,
      username: 'genome',
      password: '',
      databaseName: 'visiGene',
    },
  },
  {
    id: 'yeast-genome',
    label: 'Yeast genome',
    engine: 'MySQL',
    draft: {
      name: 'Yeast genome',
      dbType: 'mysql',
      host: 'genome-mysql.soe.ucsc.edu',
      port: 3306,
      username: 'genome',
      password: '',
      databaseName: 'sacCer3',
    },
  },
  {
    id: 'ucsc-shared',
    label: 'UCSC shared',
    engine: 'MySQL',
    draft: {
      name: 'UCSC shared',
      dbType: 'mysql',
      host: 'genome-mysql.soe.ucsc.edu',
      port: 3306,
      username: 'genome',
      password: '',
      databaseName: 'hgFixed',
    },
  },
];

/**
 * A few of them, chosen at random.
 *
 * All eight at once would be a menu where a hint belongs, and the dialog is
 * meant to be a form with a shortcut on it. Picked fresh each time the dialog
 * opens, so reopening offers something else rather than the same three.
 */
export function pickSampleConnections(count = 3): SampleConnection[] {
  const pool = [...SAMPLE_CONNECTIONS];
  for (let i = pool.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [pool[i], pool[j]] = [pool[j] as SampleConnection, pool[i] as SampleConnection];
  }
  return pool.slice(0, count);
}
