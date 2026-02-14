"""
Tests for migration system
"""

import pytest
import tempfile
import os
from pathlib import Path
import sqlite3

from migration_manager import MigrationManager, Migration


class TestMigrationManager:
    """Test migration manager functionality"""

    def test_create_migrations_table(self, tmp_path):
        """Test that migrations table is created"""
        db_path = tmp_path / "test.db"
        migrations_dir = tmp_path / "migrations"
        migrations_dir.mkdir()

        manager = MigrationManager(str(db_path), migrations_dir)

        # Check table exists
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='schema_migrations'
        """)
        result = cursor.fetchone()
        conn.close()

        assert result is not None
        assert result[0] == "schema_migrations"

    def test_discover_python_migrations(self, tmp_path):
        """Test discovering Python migration files"""
        db_path = tmp_path / "test.db"
        migrations_dir = tmp_path / "migrations"
        migrations_dir.mkdir()

        # Create test migration files
        (migrations_dir / "20260101000000_first.py").write_text("""
def up(conn):
    pass

def down(conn):
    pass
""")
        (migrations_dir / "20260102000000_second.py").write_text("""
def up(conn):
    pass
""")

        manager = MigrationManager(str(db_path), migrations_dir)
        migrations = manager.discover_migrations()

        assert len(migrations) == 2
        assert migrations[0].version == "20260101000000"
        assert migrations[1].version == "20260102000000"

    def test_discover_sql_migrations(self, tmp_path):
        """Test discovering SQL migration files"""
        db_path = tmp_path / "test.db"
        migrations_dir = tmp_path / "migrations"
        migrations_dir.mkdir()

        # Create test SQL migration
        (migrations_dir / "20260101000000_create_table.sql").write_text("""
-- up
CREATE TABLE test (id INTEGER PRIMARY KEY);

-- down
DROP TABLE test;
""")

        manager = MigrationManager(str(db_path), migrations_dir)
        migrations = manager.discover_migrations()

        assert len(migrations) == 1
        assert migrations[0].is_sql is True
        assert migrations[0].is_python is False

    def test_get_pending_migrations(self, tmp_path):
        """Test identifying pending migrations"""
        db_path = tmp_path / "test.db"
        migrations_dir = tmp_path / "migrations"
        migrations_dir.mkdir()

        # Create migrations
        (migrations_dir / "20260101000000_first.py").write_text("""
def up(conn):
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE test1 (id INTEGER)")
    conn.commit()
""")
        (migrations_dir / "20260102000000_second.py").write_text("""
def up(conn):
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE test2 (id INTEGER)")
    conn.commit()
""")

        manager = MigrationManager(str(db_path), migrations_dir)

        # Initially, all should be pending
        pending = manager.get_pending_migrations()
        assert len(pending) == 2

        # Apply first migration
        manager.apply_migration(pending[0])

        # Now only one should be pending
        pending = manager.get_pending_migrations()
        assert len(pending) == 1
        assert pending[0].version == "20260102000000"

    def test_apply_python_migration(self, tmp_path):
        """Test applying a Python migration"""
        db_path = tmp_path / "test.db"
        migrations_dir = tmp_path / "migrations"
        migrations_dir.mkdir()

        # Create migration that creates a table
        (migrations_dir / "20260101000000_create_users.py").write_text("""
def up(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )
    ''')
    conn.commit()
""")

        manager = MigrationManager(str(db_path), migrations_dir)
        migrations = manager.discover_migrations()

        # Apply migration
        exec_time = manager.apply_migration(migrations[0])
        assert exec_time >= 0

        # Verify table was created
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
        )
        result = cursor.fetchone()
        conn.close()

        assert result is not None

    def test_apply_sql_migration(self, tmp_path):
        """Test applying an SQL migration"""
        db_path = tmp_path / "test.db"
        migrations_dir = tmp_path / "migrations"
        migrations_dir.mkdir()

        # Create SQL migration
        (migrations_dir / "20260101000000_create_posts.sql").write_text("""
-- up
CREATE TABLE posts (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL
);

-- down
DROP TABLE posts;
""")

        manager = MigrationManager(str(db_path), migrations_dir)
        migrations = manager.discover_migrations()

        # Apply migration
        manager.apply_migration(migrations[0])

        # Verify table was created
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='posts'"
        )
        result = cursor.fetchone()
        conn.close()

        assert result is not None

    def test_rollback_migration(self, tmp_path):
        """Test rolling back a migration"""
        db_path = tmp_path / "test.db"
        migrations_dir = tmp_path / "migrations"
        migrations_dir.mkdir()

        # Create migration with down function
        (migrations_dir / "20260101000000_create_items.sql").write_text("""
-- up
CREATE TABLE items (id INTEGER PRIMARY KEY);

-- down
DROP TABLE items;
""")

        manager = MigrationManager(str(db_path), migrations_dir)
        migrations = manager.discover_migrations()

        # Apply migration
        manager.apply_migration(migrations[0])

        # Verify table exists
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='items'"
        )
        assert cursor.fetchone() is not None
        conn.close()

        # Rollback
        manager.rollback_migration(migrations[0])

        # Verify table is gone
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='items'"
        )
        assert cursor.fetchone() is None
        conn.close()

    def test_migrate_all_pending(self, tmp_path):
        """Test migrating all pending migrations"""
        db_path = tmp_path / "test.db"
        migrations_dir = tmp_path / "migrations"
        migrations_dir.mkdir()

        # Create multiple migrations
        for i in range(3):
            (migrations_dir / f"2026010{i}000000_migration_{i}.py").write_text(f"""
def up(conn):
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE table_{i} (id INTEGER)")
    conn.commit()
""")

        manager = MigrationManager(str(db_path), migrations_dir)

        # Migrate all
        count = manager.migrate()
        assert count == 3

        # Verify all applied
        applied = manager.get_applied_migrations()
        assert len(applied) == 3

    def test_migration_failure_rollback(self, tmp_path):
        """Test that failed migrations are rolled back"""
        db_path = tmp_path / "test.db"
        migrations_dir = tmp_path / "migrations"
        migrations_dir.mkdir()

        # Create migration that will fail
        (migrations_dir / "20260101000000_failing.py").write_text("""
def up(conn):
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE test (id INTEGER)")
    # This will fail
    cursor.execute("INVALID SQL SYNTAX")
    conn.commit()
""")

        manager = MigrationManager(str(db_path), migrations_dir)
        migrations = manager.discover_migrations()

        # Should raise an exception
        with pytest.raises(Exception):
            manager.apply_migration(migrations[0])

        # Migration should not be marked as applied
        applied = manager.get_applied_migrations()
        assert len(applied) == 0

        # Table should not exist (transaction rolled back)
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='test'"
        )
        assert cursor.fetchone() is None
        conn.close()

    def test_create_migration(self, tmp_path):
        """Test creating a new migration file"""
        db_path = tmp_path / "test.db"
        migrations_dir = tmp_path / "migrations"
        migrations_dir.mkdir()

        manager = MigrationManager(str(db_path), migrations_dir)

        # Create Python migration
        filepath = manager.create_migration("add user table", "python")

        assert filepath.exists()
        assert filepath.suffix == ".py"
        assert "add_user_table" in filepath.name

        content = filepath.read_text()
        assert "def up(conn):" in content
        assert "def down(conn):" in content

    def test_get_migration_status(self, tmp_path):
        """Test getting migration status"""
        db_path = tmp_path / "test.db"
        migrations_dir = tmp_path / "migrations"
        migrations_dir.mkdir()

        # Create migrations
        (migrations_dir / "20260101000000_first.py").write_text("def up(conn): pass")
        (migrations_dir / "20260102000000_second.py").write_text("def up(conn): pass")

        manager = MigrationManager(str(db_path), migrations_dir)

        # Apply first migration
        migrations = manager.discover_migrations()
        manager.apply_migration(migrations[0])

        # Get status
        status = manager.get_status()

        assert len(status) == 2
        assert status[0]["applied"] is True
        assert status[1]["applied"] is False


class TestMigrationClass:
    """Test Migration class"""

    def test_migration_sorting(self):
        """Test that migrations sort by version"""
        m1 = Migration("20260103000000", "third", Path("third.py"))
        m2 = Migration("20260101000000", "first", Path("first.py"))
        m3 = Migration("20260102000000", "second", Path("second.py"))

        migrations = sorted([m1, m2, m3])

        assert migrations[0].version == "20260101000000"
        assert migrations[1].version == "20260102000000"
        assert migrations[2].version == "20260103000000"

    def test_migration_file_types(self):
        """Test detecting migration file types"""
        py_migration = Migration("20260101000000", "test", Path("test.py"))
        sql_migration = Migration("20260101000000", "test", Path("test.sql"))

        assert py_migration.is_python is True
        assert py_migration.is_sql is False

        assert sql_migration.is_python is False
        assert sql_migration.is_sql is True
