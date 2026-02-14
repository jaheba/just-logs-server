#!/usr/bin/env python3
"""
CLI tool for managing database migrations
"""

import sys
import os
from pathlib import Path

# Add parent directory to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent))

from migration_manager import MigrationManager
from database import DATABASE_PATH


def print_usage():
    """Print usage information"""
    print("""
Usage: python -m migrations_cli <command> [args]

Commands:
    migrate             Apply all pending migrations
    status              Show migration status
    create <desc>       Create a new migration file
    rollback            Rollback the last migration
    help                Show this help message

Examples:
    python -m migrations_cli migrate
    python -m migrations_cli create "add user preferences table"
    python -m migrations_cli status
    python -m migrations_cli rollback
""")


def main():
    """Main CLI entry point"""
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    command = sys.argv[1].lower()

    # Initialize migration manager
    migrations_dir = Path(__file__).parent / "migrations"
    manager = MigrationManager(DATABASE_PATH, migrations_dir)

    if command == "migrate":
        # Apply all pending migrations
        try:
            count = manager.migrate()
            if count == 0:
                print("Database is up to date")
            sys.exit(0)
        except Exception as e:
            print(f"Error applying migrations: {e}")
            sys.exit(1)

    elif command == "status":
        # Show migration status
        status = manager.get_status()
        if not status:
            print("No migrations found")
            sys.exit(0)

        print("\nMigration Status:")
        print("-" * 80)
        print(f"{'Version':<16} {'Status':<10} {'Description':<40}")
        print("-" * 80)

        for m in status:
            status_str = "✓ Applied" if m["applied"] else "  Pending"
            print(f"{m['version']:<16} {status_str:<10} {m['description']:<40}")

        print("-" * 80)
        applied_count = sum(1 for m in status if m["applied"])
        pending_count = len(status) - applied_count
        print(f"Applied: {applied_count}, Pending: {pending_count}")
        print()

    elif command == "create":
        # Create a new migration file
        if len(sys.argv) < 3:
            print("Error: Please provide a migration description")
            print("Usage: python -m migrations_cli create <description>")
            sys.exit(1)

        description = " ".join(sys.argv[2:])

        # Ask for template type
        print("\nSelect migration template:")
        print("  1. Python (default)")
        print("  2. SQL")
        choice = input("\nChoice [1]: ").strip() or "1"

        template = "python" if choice == "1" else "sql"

        try:
            filepath = manager.create_migration(description, template)
            print(f"\n✓ Migration created successfully!")
            print(f"  Path: {filepath}")
            print(f"\nEdit the file and then run: python -m migrations_cli migrate")
        except Exception as e:
            print(f"Error creating migration: {e}")
            sys.exit(1)

    elif command == "rollback":
        # Rollback the last migration
        try:
            manager.rollback_last()
            print("\n✓ Rollback completed successfully")
        except Exception as e:
            print(f"Error rolling back migration: {e}")
            sys.exit(1)

    elif command in ["help", "--help", "-h"]:
        print_usage()
        sys.exit(0)

    else:
        print(f"Error: Unknown command '{command}'")
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
