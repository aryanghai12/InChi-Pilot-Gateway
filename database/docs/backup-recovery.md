# PostgreSQL Backup and Recovery Guide

## Reference environment

- Container: `inchi_postgres`
- Database: `inchi_db`
- User: `inchi_user`
- Host port: `5433`
- PostgreSQL image: `pgvector/pgvector:pg17`
- Backup format: PostgreSQL custom format (`-Fc`)

Use synthetic data only for local backup and restore verification.

## Create a backup

The following command creates a compressed custom-format dump inside the
running PostgreSQL container:

```powershell
docker exec inchi_postgres pg_dump `
  -U inchi_user `
  -d inchi_db `
  -Fc `
  -f /tmp/inchi_db_backup.dump
```

Inspect the archive:

```powershell
docker exec inchi_postgres pg_restore -l /tmp/inchi_db_backup.dump
```

## Restore into a temporary database

Use a separate database for verification. Never restore over the active
development database during a recovery test.

```powershell
docker exec inchi_postgres psql -U inchi_user -d postgres `
  -c "DROP DATABASE IF EXISTS inchi_restore_test_vishal;"

docker exec inchi_postgres psql -U inchi_user -d postgres `
  -c "CREATE DATABASE inchi_restore_test_vishal;"

docker exec inchi_postgres pg_restore `
  -U inchi_user `
  -d inchi_restore_test_vishal `
  --exit-on-error `
  /tmp/inchi_db_backup.dump
```

Verify restored data:

```powershell
docker exec inchi_postgres psql -U inchi_user -d inchi_restore_test_vishal `
  -c "SELECT 'buyer_requirement' AS table_name, COUNT(*) AS row_count FROM buyer_requirement
      UNION ALL SELECT 'buyer_requirement_version', COUNT(*) FROM buyer_requirement_version
      UNION ALL SELECT 'requirement_quantity', COUNT(*) FROM requirement_quantity
      UNION ALL SELECT 'requirement_commercial_terms', COUNT(*) FROM requirement_commercial_terms
      UNION ALL SELECT 'requirement_delivery', COUNT(*) FROM requirement_delivery
      UNION ALL SELECT 'matching_readiness_blocker', COUNT(*) FROM matching_readiness_blocker;"
```

Remove the temporary restore database after verification:

```powershell
docker exec inchi_postgres psql -U inchi_user -d postgres `
  -c "DROP DATABASE IF EXISTS inchi_restore_test_vishal;"
```

## Verification evidence

Verified on 12 November 2026 against PostgreSQL 17.11:

| Check | Result |
|---|---|
| Custom-format backup created | Passed |
| Backup archive inspected with `pg_restore -l` | Passed |
| Temporary restore database created | Passed |
| Backup restored with `--exit-on-error` | Passed |
| `buyer_requirement` rows after restore | 20 |
| `buyer_requirement_version` rows after restore | 20 |
| `requirement_quantity` rows after restore | 20 |
| `requirement_commercial_terms` rows after restore | 20 |
| `requirement_delivery` rows after restore | 20 |
| `matching_readiness_blocker` rows after restore | 15 |
| Temporary restore database removed | Passed |

Production credentials and `.env` files must never be included in a committed
backup or documentation artifact.
