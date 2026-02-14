"""
Database Migration Manager for just-logging

Handles schema versioning and migrations to enable graceful server updates.
"""

import sqlite3
import re
from pathlib import Path
from typing import List, Tuple, Optional, Callable
from datetime import datetime
import importlib.util
import sys


class Migration:
    """Represents a single database migration"""

    def __init__(self, version: str, description: str, filepath: Path):
        self.version = version
        self.description = description
        self.filepath = filepath
        self.is_python = filepath.suffix == ".py"
        self.is_sql = filepath.suffix == ".sql"

    def __repr__(self):
        return f"Migration(version={self.version}, description={self.description})"

    def __lt__(self, other):
        """Enable sorting migrations by version"""
        return self.version < other.version


class MigrationManager:
    """Manages database migrations"""

    MIGRATIONS_TABLE = "schema_migrations"

    def __init__(self, db_path: str, migrations_dir: Optional[Path] = None):
        self.db_path = db_path
        if migrations_dir is None:
            # Default to migrations directory relative to this file
            self.migrations_dir = Path(__file__).parent / "migrations"
        else:
            self.migrations_dir = Path(migrations_dir)

        self.migrations_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_migrations_table()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_migrations_table(self):
        """Create the schema_migrations table if it doesn't exist"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {self.MIGRATIONS_TABLE} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version TEXT UNIQUE NOT NULL,
                    description TEXT NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    execution_time_ms INTEGER
                )
            """)
            cursor.execute(f"""
                CREATE INDEX IF NOT EXISTS idx_migrations_version 
                ON {self.MIGRATIONS_TABLE}(version)
            """)
            conn.commit()
        finally:
            conn.close()

    def _parse_migration_filename(self, filename: str) -> Optional[Tuple[str, str]]:
        """
        Parse migration filename to extract version and description
        Format: YYYYMMDDHHMMSS_description.py or .sql
        Returns: (version, description) or None if invalid format
        """
        # Match timestamp_description pattern
        match = re.match(r"^(\d{14})_(.+)\.(py|sql)$", filename)
        if match:
            version = match.group(1)
            description = match.group(2).replace("_", " ")
            return (version, description)
        return None

    def discover_migrations(self) -> List[Migration]:
        """Discover all migration files in the migrations directory"""
        migrations = []

        # Find all .py and .sql files in migrations directory
        for filepath in self.migrations_dir.glob("*"):
            if filepath.name.startswith("__") or filepath.name == "README.md":
                continue

            if filepath.suffix in [".py", ".sql"]:
                parsed = self._parse_migration_filename(filepath.name)
                if parsed:
                    version, description = parsed
                    migrations.append(Migration(version, description, filepath))

        return sorted(migrations)

    def get_applied_migrations(self) -> List[str]:
        """Get list of applied migration versions"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT version FROM {self.MIGRATIONS_TABLE} ORDER BY version"
            )
            return [row[0] for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_pending_migrations(self) -> List[Migration]:
        """Get list of migrations that haven't been applied yet"""
        all_migrations = self.discover_migrations()
        applied = set(self.get_applied_migrations())
        return [m for m in all_migrations if m.version not in applied]

    def _load_python_migration(
        self, migration: Migration
    ) -> Tuple[Callable, Optional[Callable]]:
        """Load up and down functions from a Python migration file"""
        spec = importlib.util.spec_from_file_location(
            f"migration_{migration.version}", migration.filepath
        )
        if spec is None or spec.loader is None:
            raise Exception(f"Could not load migration: {migration.filepath}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[f"migration_{migration.version}"] = module
        spec.loader.exec_module(module)

        if not hasattr(module, "up"):
            raise Exception(f"Migration {migration.version} missing 'up' function")

        up_func = module.up
        down_func = getattr(module, "down", None)

        return up_func, down_func

    def _load_sql_migration(self, migration: Migration) -> Tuple[str, Optional[str]]:
        """Load up and down SQL from a SQL migration file"""
        content = migration.filepath.read_text()

        # Split on -- up and -- down markers
        up_sql = None
        down_sql = None

        # Simple parser for -- up and -- down sections
        lines = content.split("\n")
        current_section = None
        up_lines = []
        down_lines = []

        for line in lines:
            stripped = line.strip().lower()
            if stripped == "-- up":
                current_section = "up"
                continue
            elif stripped == "-- down":
                current_section = "down"
                continue

            if current_section == "up":
                up_lines.append(line)
            elif current_section == "down":
                down_lines.append(line)

        up_sql = "\n".join(up_lines).strip()
        down_sql = "\n".join(down_lines).strip() if down_lines else None

        if not up_sql:
            raise Exception(f"Migration {migration.version} missing '-- up' section")

        return up_sql, down_sql

    def apply_migration(self, migration: Migration) -> int:
        """
        Apply a single migration
        Returns: execution time in milliseconds
        """
        print(f"Applying migration {migration.version}: {migration.description}")

        conn = self._get_connection()
        start_time = datetime.now()

        try:
            # Begin transaction
            conn.execute("BEGIN")

            if migration.is_python:
                # Load and execute Python migration
                up_func, _ = self._load_python_migration(migration)
                up_func(conn)
            elif migration.is_sql:
                # Load and execute SQL migration
                up_sql, _ = self._load_sql_migration(migration)
                cursor = conn.cursor()
                # Execute all statements in the SQL
                cursor.executescript(up_sql)

            # Record migration as applied
            cursor = conn.cursor()
            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
            cursor.execute(
                f"""
                INSERT INTO {self.MIGRATIONS_TABLE} 
                (version, description, execution_time_ms)
                VALUES (?, ?, ?)
                """,
                (migration.version, migration.description, execution_time),
            )

            # Commit transaction
            conn.commit()
            print(f"  ✓ Applied successfully ({execution_time}ms)")
            return execution_time

        except Exception as e:
            conn.rollback()
            print(f"  ✗ Failed: {e}")
            raise
        finally:
            conn.close()

    def rollback_migration(self, migration: Migration):
        """
        Rollback a single migration
        Note: Only works if migration has a down function/section
        """
        print(f"Rolling back migration {migration.version}: {migration.description}")

        conn = self._get_connection()

        try:
            # Begin transaction
            conn.execute("BEGIN")

            if migration.is_python:
                # Load and execute Python migration
                _, down_func = self._load_python_migration(migration)
                if down_func is None:
                    raise Exception(
                        f"Migration {migration.version} has no 'down' function"
                    )
                down_func(conn)
            elif migration.is_sql:
                # Load and execute SQL migration
                _, down_sql = self._load_sql_migration(migration)
                if not down_sql:
                    raise Exception(
                        f"Migration {migration.version} has no '-- down' section"
                    )
                cursor = conn.cursor()
                cursor.executescript(down_sql)

            # Remove migration from applied list
            cursor = conn.cursor()
            cursor.execute(
                f"DELETE FROM {self.MIGRATIONS_TABLE} WHERE version = ?",
                (migration.version,),
            )

            # Commit transaction
            conn.commit()
            print(f"  ✓ Rolled back successfully")

        except Exception as e:
            conn.rollback()
            print(f"  ✗ Rollback failed: {e}")
            raise
        finally:
            conn.close()

    def migrate(self) -> int:
        """
        Apply all pending migrations
        Returns: number of migrations applied
        """
        pending = self.get_pending_migrations()

        if not pending:
            print("No pending migrations")
            return 0

        print(f"Found {len(pending)} pending migration(s)")

        for migration in pending:
            self.apply_migration(migration)

        print(f"\n✓ Applied {len(pending)} migration(s) successfully")
        return len(pending)

    def rollback_last(self):
        """Rollback the most recently applied migration"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT version FROM {self.MIGRATIONS_TABLE} ORDER BY version DESC LIMIT 1"
            )
            row = cursor.fetchone()

            if not row:
                print("No migrations to rollback")
                return

            version = row[0]
        finally:
            conn.close()

        # Find the migration file
        all_migrations = self.discover_migrations()
        migration = next((m for m in all_migrations if m.version == version), None)

        if not migration:
            raise Exception(f"Could not find migration file for version {version}")

        self.rollback_migration(migration)

    def get_status(self) -> List[dict]:
        """Get status of all migrations"""
        all_migrations = self.discover_migrations()
        applied = set(self.get_applied_migrations())

        status = []
        for migration in all_migrations:
            status.append(
                {
                    "version": migration.version,
                    "description": migration.description,
                    "applied": migration.version in applied,
                    "filepath": str(migration.filepath),
                }
            )

        return status

    def create_migration(self, description: str, template: str = "python") -> Path:
        """
        Create a new migration file with the given description
        Returns: path to the created file
        """
        # Generate version from current timestamp
        version = datetime.now().strftime("%Y%m%d%H%M%S")

        # Sanitize description for filename
        filename_desc = re.sub(r"[^a-z0-9]+", "_", description.lower()).strip("_")

        # Create filename
        extension = "py" if template == "python" else "sql"
        filename = f"{version}_{filename_desc}.{extension}"
        filepath = self.migrations_dir / filename

        # Create template content
        if template == "python":
            content = f'''"""
Description: {description}
"""

def up(conn):
    """Apply the migration"""
    cursor = conn.cursor()
    # TODO: Implement migration
    cursor.execute("-- Your SQL here")
    conn.commit()


def down(conn):
    """Rollback the migration"""
    cursor = conn.cursor()
    # TODO: Implement rollback
    cursor.execute("-- Your rollback SQL here")
    conn.commit()
'''
        else:  # SQL template
            content = f"""-- Description: {description}

-- up


-- down

"""

        filepath.write_text(content)
        print(f"Created migration: {filepath}")
        return filepath
