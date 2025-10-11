export interface DatabaseConfig {
  key: string;
  source: string;
  errorPrefix: string;
}

export const DATABASE_CONFIGS: DatabaseConfig[] = [
  { key: 'IMO_DB', source: 'imo', errorPrefix: 'IMO' },
  { key: 'PUTNAM_DB', source: 'putnam', errorPrefix: 'Putnam' },
  { key: 'MIT_DB', source: 'mit', errorPrefix: 'MIT' },
];
