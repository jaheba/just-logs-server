# Database Migrations Guide

This document describes the database migration system for just-logging.

## Overview

The migration system provides:
- **Version tracking** - Track which migrations have been applied
- **Automatic execution** - Migrations run automatically on server startup
- **Rollback support** - Ability to undo migrations when possible
- **Multiple formats** - Support for both Python and SQL migrations
- **CLI tools** - Command-line interface for migration management

## How It Works

1. **Migration Files** - Stored in `backend/migrations/` directory
2. **Tracking Table** - `schema_migrations` table tracks applied migrations
3. **Automatic Execution** - Migrations run during server startup via `init_database()`
4. **Sequential Application** - Migrations are applied in order by timestamp

## Migration File Format

Migrations follow the naming convention:
```
YYYYMMDDHHMMSS_description.{py|sql}
```

Example: `20260214120000_add_user_preferences.py`

### Python Migrations

Python migrations provide full programmatic control:

```python
"""
Description: Add user preferences table
"""

def up(conn):
    """Apply the migration"""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            preferences TEXT,
            FOREIGN KEY (user_id) REFERENCES web_users(id)
        )
    """)
    conn.commit()


def down(conn):
    """Rollback the migration"""
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS user_preferences")
    conn.commit()
```

### SQL Migrations

SQL migrations are simpler for straightforward schema changes:

```sql
-- Description: Add user preferences table

-- up
CREATE TABLE user_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    preferences TEXT,
    FOREIGN KEY (user_id) REFERENCES web_users(id)
);

-- down
DROP TABLE IF EXISTS user_preferences;
```

## Using the Migration CLI

### Check Migration Status

```bash
python -m backend.migrations_cli status
```

This shows:
- All discovered migration files
- Which migrations have been applied
- Which migrations are pending

### Apply Pending Migrations

```bash
python -m backend.migrations_cli migrate
```

This will:
- Find all pending migrations
- Apply them in order
- Track them in the `schema_migrations` table
- Show execution time for each

### Create a New Migration

```bash
python -m backend.migrations_cli create "add user preferences table"
```

This will:
- Generate a timestamped migration file
- Prompt you to choose Python or SQL format
- Create a template file in `backend/migrations/`
- Show the file path for editing

### Rollback Last Migration

```bash
python -m backend.migrations_cli rollback
```

This will:
- Find the most recently applied migration
- Execute its `down()` function or `-- down` section
- Remove it from the applied migrations list

**Note**: Rollback only works if the migration has a down function/section.

## Automatic Migration on Startup

When the server starts, `init_database()` automatically:
1. Applies SQLite performance optimizations
2. Runs all pending migrations
3. Continues with normal startup

This means you can deploy new code with migrations, and they'll be applied automatically when the server restarts.

## Best Practices

### 1. Always Test Migrations

Test migrations on a backup database first:

```bash
# Backup your database
cp jlo.db jlo.db.backup

# Test migration
python -m backend.migrations_cli migrate

# If something goes wrong
mv jlo.db.backup jlo.db
```

### 2. Keep Migrations Small

One logical change per migration:
- ✅ Good: `add_user_email_column.py`
- ❌ Bad: `update_schema_with_lots_of_changes.py`

### 3. Make Migrations Reversible

Always implement `down()` when possible:

```python
def up(conn):
    cursor = conn.cursor()
    cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
    conn.commit()

def down(conn):
    # SQLite limitation - can't drop columns easily
    raise NotImplementedError("Cannot remove column without recreating table")
```

### 4. Handle SQLite Limitations

SQLite has limitations for schema changes:
- ✅ Can: Add columns
- ✅ Can: Create tables/indexes
- ❌ Cannot: Drop columns (requires table recreation)
- ❌ Cannot: Modify column types (requires table recreation)

For complex changes, recreate the table:

```python
def up(conn):
    cursor = conn.cursor()
    
    # Create new table with updated schema
    cursor.execute("""
        CREATE TABLE users_new (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            email TEXT NOT NULL  -- Added NOT NULL constraint
        )
    """)
    
    # Copy data
    cursor.execute("INSERT INTO users_new SELECT * FROM users")
    
    # Swap tables
    cursor.execute("DROP TABLE users")
    cursor.execute("ALTER TABLE users_new RENAME TO users")
    
    conn.commit()
```

### 5. Document Complex Migrations

Add comments explaining the purpose and any gotchas:

```python
"""
Description: Migrate user roles from boolean to enum

This migration updates the user_roles table to use a TEXT enum
instead of is_admin boolean. Existing admins are migrated to 
'admin' role, others to 'viewer'.

Note: This migration cannot be easily rolled back due to data
transformation. Backup your database first!
"""
```

### 6. Use Transactions

Migrations are automatically wrapped in transactions, but you can control commit behavior:

```python
def up(conn):
    cursor = conn.cursor()
    
    # Multiple operations in one transaction
    cursor.execute("CREATE TABLE ...")
    cursor.execute("CREATE INDEX ...")
    
    # Only commit at the end
    conn.commit()
```

### 7. Test Both Up and Down

Always test both directions:

```bash
# Apply migration
python -m backend.migrations_cli migrate

# Verify it worked
# ... check database ...

# Rollback
python -m backend.migrations_cli rollback

# Verify rollback worked
# ... check database ...

# Re-apply
python -m backend.migrations_cli migrate
```

## Migration Workflow

### Development

1. Make schema changes by creating a migration:
   ```bash
   python -m backend.migrations_cli create "add feature X"
   ```

2. Edit the generated migration file

3. Test the migration:
   ```bash
   python -m backend.migrations_cli migrate
   ```

4. Verify your changes work

5. Commit the migration file to version control

### Production Deployment

1. Deploy new code (including migration files)

2. Restart the server - migrations run automatically

3. Monitor logs for migration success

4. If issues occur:
   - Stop the server
   - Restore database backup
   - Fix migration
   - Redeploy

## Advanced Usage

### Running Migrations Programmatically

```python
from migration_manager import MigrationManager

manager = MigrationManager("path/to/db.db", "path/to/migrations/")

# Check status
pending = manager.get_pending_migrations()
print(f"Found {len(pending)} pending migrations")

# Apply migrations
count = manager.migrate()
print(f"Applied {count} migrations")

# Get detailed status
status = manager.get_status()
for m in status:
    print(f"{m['version']}: {'Applied' if m['applied'] else 'Pending'}")
```

### Custom Migration Location

```python
from pathlib import Path
from migration_manager import MigrationManager

custom_dir = Path("/custom/migrations/path")
manager = MigrationManager("db.db", custom_dir)
manager.migrate()
```

## Troubleshooting

### Migration Failed During Apply

If a migration fails:
1. The transaction is rolled back automatically
2. The migration is NOT marked as applied
3. Fix the migration file
4. Run `migrate` again

### Migration Marked as Applied But Didn't Complete

This shouldn't happen (transactions prevent it), but if it does:
1. Manually remove from `schema_migrations` table:
   ```sql
   DELETE FROM schema_migrations WHERE version = '20260214120000';
   ```
2. Fix the migration
3. Run `migrate` again

### Need to Skip a Migration

If you need to mark a migration as applied without running it:
```sql
INSERT INTO schema_migrations (version, description)
VALUES ('20260214120000', 'description here');
```

### Migrations Not Running on Startup

Check:
1. Migration files are in `backend/migrations/`
2. Files follow naming convention
3. Check server logs for error messages

## Examples

### Example 1: Add a Simple Column

```sql
-- Description: Add last_login_ip to web_users

-- up
ALTER TABLE web_users ADD COLUMN last_login_ip TEXT;

-- down
-- Cannot drop column in SQLite without recreating table
```

### Example 2: Create a New Table

```python
"""
Description: Add session tracking table
"""

def up(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_token TEXT UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES web_users(id) ON DELETE CASCADE
        )
    """)
    cursor.execute("""
        CREATE INDEX idx_sessions_token ON user_sessions(session_token)
    """)
    cursor.execute("""
        CREATE INDEX idx_sessions_user ON user_sessions(user_id, expires_at)
    """)
    conn.commit()

def down(conn):
    cursor = conn.cursor()
    cursor.execute("DROP INDEX IF EXISTS idx_sessions_user")
    cursor.execute("DROP INDEX IF EXISTS idx_sessions_token")
    cursor.execute("DROP TABLE IF EXISTS user_sessions")
    conn.commit()
```

### Example 3: Data Migration

```python
"""
Description: Migrate log levels to standardized format

Changes: ERROR -> error, WARNING -> warn, INFO -> info
"""

def up(conn):
    cursor = conn.cursor()
    
    # Update log levels to lowercase
    cursor.execute("UPDATE logs SET level = LOWER(level)")
    
    # Standardize WARNING to warn
    cursor.execute("UPDATE logs SET level = 'warn' WHERE level = 'warning'")
    
    conn.commit()

def down(conn):
    cursor = conn.cursor()
    
    # Restore original format
    cursor.execute("UPDATE logs SET level = UPPER(level)")
    cursor.execute("UPDATE logs SET level = 'WARNING' WHERE level = 'WARN'")
    
    conn.commit()
```

## Architecture

### Components

1. **MigrationManager** (`backend/migration_manager.py`)
   - Core migration engine
   - Handles discovery, tracking, and execution

2. **CLI Tool** (`backend/migrations_cli.py`)
   - Command-line interface
   - User-friendly commands

3. **Integration** (`backend/database.py`)
   - Integrates with `init_database()`
   - Runs automatically on startup

4. **Migration Files** (`backend/migrations/*.{py,sql}`)
   - Individual migration definitions
   - Version-controlled schema changes

### Database Schema

The `schema_migrations` table tracks applied migrations:

```sql
CREATE TABLE schema_migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT UNIQUE NOT NULL,
    description TEXT NOT NULL,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    execution_time_ms INTEGER
);
```

### Execution Flow

```
Server Startup
    ↓
init_database()
    ↓
Apply SQLite Optimizations
    ↓
MigrationManager.migrate()
    ↓
Discover Migration Files
    ↓
Check schema_migrations Table
    ↓
Find Pending Migrations
    ↓
For Each Pending Migration:
    ↓
    Begin Transaction
    ↓
    Execute up() or -- up
    ↓
    Record in schema_migrations
    ↓
    Commit Transaction
    ↓
Continue Startup
```

## Future Enhancements

Potential improvements:
- Web UI for viewing migration status
- Dry-run mode to preview changes
- Migration dependencies/prerequisites
- Automatic backup before migration
- Migration linting/validation
- Support for data validation after migration
