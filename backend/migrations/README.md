# Database Migrations

This directory contains database migration files for just-logging.

## Migration File Format

Migration files should follow the naming convention:
```
YYYYMMDDHHMMSS_description.py
```

Example: `20260214120000_add_tags_column.py`

## Creating a New Migration

### Python Migration

Create a Python file with `up()` and `down()` functions:

```python
"""
Description: Add tags column to logs table
"""

def up(conn):
    """Apply the migration"""
    cursor = conn.cursor()
    cursor.execute("ALTER TABLE logs ADD COLUMN tags TEXT")
    conn.commit()

def down(conn):
    """Rollback the migration"""
    # SQLite doesn't support DROP COLUMN easily
    # Document if rollback is not possible
    raise NotImplementedError("Cannot remove column in SQLite")
```

### SQL Migration

Create a SQL file with `-- up` and `-- down` sections:

```sql
-- Description: Add tags column to logs table

-- up
ALTER TABLE logs ADD COLUMN tags TEXT;

-- down
-- Cannot remove column in SQLite without recreating table
```

## Running Migrations

Migrations are automatically run on server startup. You can also run them manually:

```bash
# Apply all pending migrations
python -m backend.migrations.cli migrate

# Create a new migration
python -m backend.migrations.cli create "add_new_column"

# Show migration status
python -m backend.migrations.cli status

# Rollback last migration
python -m backend.migrations.cli rollback
```

## Migration Best Practices

1. **Always test migrations** on a backup database first
2. **Make migrations reversible** when possible
3. **Keep migrations small** - one logical change per migration
4. **Document complex changes** in the migration file
5. **Back up your database** before running migrations in production
6. **Test both up and down** functions
7. **Use transactions** - migrations are wrapped in transactions automatically
