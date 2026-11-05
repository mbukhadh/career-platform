# Railway database backup and restore test, 2026-10-29

Done before moving the site from Railway to AWS (EC2 + RDS). Claude Code ran
the commands; results below are copied from their output.

## Source

| | |
| --- | --- |
| Railway project | `wholesome-solace`, environment `production` |
| App service | `career-platform`, custom domain `mjbukhadhour.com`, repo `mbukhadh/career-platform` |
| Database service | `Postgres` (image `postgres-ssl:18`), server 18.6 |
| Size | 8326 kB, 10 tables, Alembic version `0001_initial_schema` |

Railway was only read from. Nothing on Railway was changed except registering
an SSH key (`mac-railway-cli`) so the CLI tunnel could open.

## Backup

Method from Railway's guide ([Back Up and Restore Postgres](https://docs.railway.com/guides/postgres-backups-restores)):
`railway connect Postgres --tunnel-only`, then

```bash
pg_dump --format=custom --no-owner --file=railway-20261029T222355Z.dump
```

| | |
| --- | --- |
| Tool | `pg_dump` 18.6 (Postgres.app), same major version as the server |
| File | `~/Backups/career-platform/railway-20261029T222355Z.dump` (outside the repo, mode 600) |
| Size | 21,620 bytes |
| SHA-256 | `f15f9a6bf5511446e1b1a817736ac2a1db4ff57d2c2996ddd3ce24bca66b2bdd` |
| Time | 8.1 s |
| Contents | data for all 10 tables (`pg_restore --list`) |

## Restore test

Restored into a new, empty local database `restore_test` (Postgres.app 18.6),
not into Railway:

```bash
pg_restore -d restore_test --no-owner --no-privileges --exit-on-error <dump>
```

Finished with no errors in 0.05 s.

## Comparison: Railway vs. restored copy

Row count and an MD5 of every row (sorted) per table, run on both sides:

| Table | Railway | Restored | Match |
| --- | ---: | ---: | --- |
| alembic_version | 1 | 1 | yes |
| contact_configurations | 1 | 1 | yes |
| education | 1 | 1 | yes |
| experience_accomplishments | 0 | 0 | yes |
| experiences | 1 | 1 | yes |
| owners | 1 | 1 | yes |
| profiles | 1 | 1 | yes |
| projects | 1 | 1 | yes |
| skill_groups | 1 | 1 | yes |
| skills | 2 | 2 | yes |

- Data: all 10 tables match on row count and checksum.
- Schema: `pg_dump --schema-only` of both is identical (160 lines, comments removed).
- App: the app pointed at `restore_test` returned 200 on `/` with footer
  `Projects source: database`.

## Recovery numbers

- Recovery point: the dump is as fresh as its timestamp, 2026-10-29 22:23:55 UTC.
  Changes made on Railway after that are not in it.
- Recovery time: about 10 s for this database (8 s dump + under 1 s restore),
  not counting setup.

## Not tested

- Restoring into RDS. That is the next step of the migration.
- Railway's own volume backups and point-in-time recovery. They are deleted
  with the project, so the dump file is the backup that survives leaving Railway.
