import sqlite3
import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from contextlib import contextmanager
from pathlib import Path


DATABASE_PATH = os.getenv("JLO_DB_PATH", "jlo.db")


@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database():
    """Initialize database with schema using migrations"""
    # Apply SQLite optimizations first
    with get_db() as conn:
        cursor = conn.cursor()

        # ============================================================
        # PERFORMANCE OPTIMIZATION: Enable WAL mode and tuning
        # ============================================================
        # Enable WAL mode for concurrent reads/writes (5-10x improvement)
        cursor.execute("PRAGMA journal_mode=WAL")

        # Balanced durability - sync at checkpoints, not every commit (10-20x improvement)
        cursor.execute("PRAGMA synchronous=NORMAL")

        # Larger page cache - 64MB (increase if you have more RAM)
        cursor.execute("PRAGMA cache_size=-64000")

        # Auto-checkpoint at 1000 pages (~4MB)
        cursor.execute("PRAGMA wal_autocheckpoint=1000")

        # Store temp tables in memory for better performance
        cursor.execute("PRAGMA temp_store=MEMORY")

        # Increase page size for better throughput (must be set before tables)
        # Note: This only affects NEW databases, existing DBs keep their page size
        cursor.execute("PRAGMA page_size=4096")

        print("SQLite optimizations applied:")
        print(
            f"  - Journal mode: {cursor.execute('PRAGMA journal_mode').fetchone()[0]}"
        )
        print(f"  - Synchronous: {cursor.execute('PRAGMA synchronous').fetchone()[0]}")
        print(
            f"  - Cache size: {cursor.execute('PRAGMA cache_size').fetchone()[0]} pages"
        )
        # ============================================================

    # Run database migrations
    from migration_manager import MigrationManager

    migrations_dir = Path(__file__).parent / "migrations"
    manager = MigrationManager(DATABASE_PATH, migrations_dir)

    print("\nRunning database migrations...")
    manager.migrate()


# App operations
def create_app(name: str) -> int:
    """Create a new application"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO apps (name) VALUES (?)", (name,))
        return cursor.lastrowid


def get_app_by_id(app_id: int) -> Optional[Dict[str, Any]]:
    """Get app by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM apps WHERE id = ?", (app_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_app_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Get app by name"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM apps WHERE name = ?", (name,))
        row = cursor.fetchone()
        return dict(row) if row else None


def list_apps() -> List[Dict[str, Any]]:
    """List all applications"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM apps ORDER BY created_at DESC")
        return [dict(row) for row in cursor.fetchall()]


# API Key operations
def create_api_key(key: str, app_id: int) -> int:
    """Create a new API key"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO api_keys (key, app_id) VALUES (?, ?)", (key, app_id)
        )
        return cursor.lastrowid


def get_api_key(key: str) -> Optional[Dict[str, Any]]:
    """Get API key details"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT ak.*, a.name as app_name 
            FROM api_keys ak
            JOIN apps a ON ak.app_id = a.id
            WHERE ak.key = ? AND ak.is_active = 1
        """,
            (key,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        api_key_data = dict(row)
        # Add tags
        api_key_data["tags"] = get_api_key_tags(api_key_data["id"])
        return api_key_data


def list_api_keys() -> List[Dict[str, Any]]:
    """List all API keys"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT ak.*, a.name as app_name 
            FROM api_keys ak
            JOIN apps a ON ak.app_id = a.id
            ORDER BY ak.created_at DESC
        """)
        keys = [dict(row) for row in cursor.fetchall()]
        # Add tags for each key
        for key in keys:
            key["tags"] = get_api_key_tags(key["id"])
        return keys


def revoke_api_key(key_id: int) -> bool:
    """Revoke an API key"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE api_keys SET is_active = 0 WHERE id = ?", (key_id,))
        return cursor.rowcount > 0


# API Key Tag operations
def create_api_key_tag(api_key_id: int, tag_key: str, tag_value: str) -> int:
    """Create a tag for an API key"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO api_key_tags (api_key_id, tag_key, tag_value) VALUES (?, ?, ?)",
            (api_key_id, tag_key, tag_value),
        )
        return cursor.lastrowid


def get_api_key_tags(api_key_id: int) -> Dict[str, str]:
    """Get all tags for an API key as a dictionary"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT tag_key, tag_value FROM api_key_tags WHERE api_key_id = ?",
            (api_key_id,),
        )
        return {row["tag_key"]: row["tag_value"] for row in cursor.fetchall()}


def delete_api_key_tag(tag_id: int) -> bool:
    """Delete a specific tag"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM api_key_tags WHERE id = ?", (tag_id,))
        return cursor.rowcount > 0


def delete_all_api_key_tags(api_key_id: int) -> bool:
    """Delete all tags for an API key"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM api_key_tags WHERE api_key_id = ?", (api_key_id,))
        return cursor.rowcount > 0


def update_api_key_tags(api_key_id: int, tags: Dict[str, str]) -> bool:
    """Update all tags for an API key (replaces existing tags)"""
    with get_db() as conn:
        cursor = conn.cursor()
        # Delete all existing tags
        cursor.execute("DELETE FROM api_key_tags WHERE api_key_id = ?", (api_key_id,))
        # Insert new tags
        for tag_key, tag_value in tags.items():
            cursor.execute(
                "INSERT INTO api_key_tags (api_key_id, tag_key, tag_value) VALUES (?, ?, ?)",
                (api_key_id, tag_key, tag_value),
            )
        return True


# Log operations
def create_log(
    app_id: int,
    level: str,
    message: str,
    structured_data: Optional[Dict[str, Any]],
    timestamp: datetime,
    tags: Optional[Dict[str, str]] = None,
) -> int:
    """Create a new log entry"""
    with get_db() as conn:
        cursor = conn.cursor()
        structured_json = json.dumps(structured_data) if structured_data else None
        tags_json = json.dumps(tags) if tags else None
        cursor.execute(
            """
            INSERT INTO logs (app_id, level, message, structured_data, tags, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (app_id, level, message, structured_json, tags_json, timestamp.isoformat()),
        )
        return cursor.lastrowid


def create_logs_bulk(logs: List[Dict[str, Any]]) -> List[int]:
    """
    Bulk insert logs in a single transaction for high-performance ingestion.
    This is 100-1000x faster than individual inserts.

    Args:
        logs: List of log dictionaries with keys:
            - app_id: int
            - level: str
            - message: str
            - structured_data: Optional[Dict[str, Any]]
            - tags: Optional[Dict[str, str]]
            - timestamp: datetime

    Returns:
        List of inserted log IDs
    """
    if not logs:
        return []

    with get_db() as conn:
        cursor = conn.cursor()

        # Prepare all data for bulk insert
        values = []
        for log in logs:
            structured_json = (
                json.dumps(log.get("structured_data"))
                if log.get("structured_data")
                else None
            )
            tags_json = json.dumps(log.get("tags")) if log.get("tags") else None
            values.append(
                (
                    log["app_id"],
                    log["level"],
                    log["message"],
                    structured_json,
                    tags_json,
                    log["timestamp"].isoformat()
                    if isinstance(log["timestamp"], datetime)
                    else log["timestamp"],
                )
            )

        # Single transaction, multiple inserts using executemany
        cursor.executemany(
            """
            INSERT INTO logs (app_id, level, message, structured_data, tags, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            values,
        )

        # Calculate inserted IDs
        # Note: With executemany, lastrowid might be None, so we query for the IDs
        if cursor.lastrowid:
            # If lastrowid is available, use it (fast path)
            last_id = cursor.lastrowid
            first_id = last_id - len(logs) + 1
            return list(range(first_id, last_id + 1))
        else:
            # Fallback: query for recent IDs (slower but reliable)
            # Get the IDs of logs we just inserted by timestamp
            cursor.execute(
                """
                SELECT id FROM logs 
                ORDER BY id DESC 
                LIMIT ?
                """,
                (len(logs),),
            )
            ids = [row[0] for row in cursor.fetchall()]
            ids.reverse()  # Return in insertion order
            return ids


def query_logs(
    app_id: Optional[int] = None,
    level: Optional[Union[str, List[str]]] = None,
    search: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    tags: Optional[Dict[str, str]] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """Query logs with filters"""
    with get_db() as conn:
        cursor = conn.cursor()

        query = """
            SELECT l.*, a.name as app_name
            FROM logs l
            JOIN apps a ON l.app_id = a.id
            WHERE 1=1
        """
        params = []

        if app_id is not None:
            query += " AND l.app_id = ?"
            params.append(app_id)

        if level is not None:
            if isinstance(level, list):
                placeholders = ",".join(["?" for _ in level])
                query += f" AND l.level IN ({placeholders})"
                params.extend(level)
            else:
                query += " AND l.level = ?"
                params.append(level)

        if search is not None:
            query += " AND l.message LIKE ?"
            params.append(f"%{search}%")

        if start_time is not None:
            query += " AND l.timestamp >= ?"
            params.append(start_time.isoformat())

        if end_time is not None:
            query += " AND l.timestamp <= ?"
            params.append(end_time.isoformat())

        # Filter by tags
        if tags:
            for tag_key, tag_value in tags.items():
                query += f" AND json_extract(l.tags, '$.{tag_key}') = ?"
                params.append(tag_value)

        query += " ORDER BY l.timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()

        results = []
        for row in rows:
            log_dict = dict(row)
            if log_dict.get("structured_data"):
                log_dict["structured_data"] = json.loads(log_dict["structured_data"])
            if log_dict.get("parsed_fields"):
                log_dict["parsed_fields"] = json.loads(log_dict["parsed_fields"])
            if log_dict.get("tags"):
                log_dict["tags"] = json.loads(log_dict["tags"])
            results.append(log_dict)

        return results


def count_logs(
    app_id: Optional[int] = None,
    level: Optional[Union[str, List[str]]] = None,
    search: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    tags: Optional[Dict[str, str]] = None,
) -> int:
    """Count logs matching filters"""
    with get_db() as conn:
        cursor = conn.cursor()

        query = "SELECT COUNT(*) as count FROM logs WHERE 1=1"
        params = []

        if app_id is not None:
            query += " AND app_id = ?"
            params.append(app_id)

        if level is not None:
            if isinstance(level, list):
                placeholders = ",".join(["?" for _ in level])
                query += f" AND level IN ({placeholders})"
                params.extend(level)
            else:
                query += " AND level = ?"
                params.append(level)

        if search is not None:
            query += " AND message LIKE ?"
            params.append(f"%{search}%")

        if start_time is not None:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())

        if end_time is not None:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())

        # Filter by tags
        if tags:
            for tag_key, tag_value in tags.items():
                query += f" AND json_extract(tags, '$.{tag_key}') = ?"
                params.append(tag_value)

        cursor.execute(query, params)
        return cursor.fetchone()["count"]


def get_all_log_tags() -> Dict[str, List[str]]:
    """Get all unique tag keys and their values from logs"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT tags FROM logs WHERE tags IS NOT NULL
        """)

        tags_dict = {}
        for row in cursor.fetchall():
            if row["tags"]:
                try:
                    tags = json.loads(row["tags"])
                    for key, value in tags.items():
                        if key not in tags_dict:
                            tags_dict[key] = set()
                        tags_dict[key].add(value)
                except json.JSONDecodeError:
                    pass

        # Convert sets to lists
        return {key: sorted(list(values)) for key, values in tags_dict.items()}


# Web user operations
def create_web_user(
    username: str,
    password_hash: str,
    email: Optional[str] = None,
    full_name: Optional[str] = None,
    role: str = "viewer",
    is_active: bool = True,
) -> int:
    """Create a web user"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO web_users 
            (username, password_hash, email, full_name, role, is_active) 
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (username, password_hash, email, full_name, role, is_active),
        )
        return cursor.lastrowid


def get_web_user(username: str) -> Optional[Dict[str, Any]]:
    """Get web user by username"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM web_users WHERE username = ?", (username,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_web_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Get web user by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM web_users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def list_web_users() -> List[Dict[str, Any]]:
    """List all web users"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM web_users ORDER BY created_at DESC")
        return [dict(row) for row in cursor.fetchall()]


def update_web_user(
    user_id: int,
    email: Optional[str] = None,
    full_name: Optional[str] = None,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> bool:
    """Update web user details"""
    with get_db() as conn:
        cursor = conn.cursor()

        updates = []
        params = []

        if email is not None:
            updates.append("email = ?")
            params.append(email)

        if full_name is not None:
            updates.append("full_name = ?")
            params.append(full_name)

        if role is not None:
            updates.append("role = ?")
            params.append(role)

        if is_active is not None:
            updates.append("is_active = ?")
            params.append(is_active)

        if not updates:
            return False

        params.append(user_id)
        query = f"UPDATE web_users SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        return cursor.rowcount > 0


def update_user_password(user_id: int, password_hash: str) -> bool:
    """Update user password"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE web_users SET password_hash = ? WHERE id = ?",
            (password_hash, user_id),
        )
        return cursor.rowcount > 0


def update_last_login(user_id: int) -> bool:
    """Update user's last login timestamp"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE web_users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
            (user_id,),
        )
        return cursor.rowcount > 0


def delete_web_user(user_id: int) -> bool:
    """Delete a web user"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM web_users WHERE id = ?", (user_id,))
        return cursor.rowcount > 0


# Parsing rule operations
def create_parsing_rule(
    app_id: Optional[int],
    name: str,
    parser_type: str,
    pattern: str,
    field_mappings: Optional[Dict[str, Any]] = None,
    enabled: bool = True,
    priority: int = 0,
) -> int:
    """Create a parsing rule"""
    with get_db() as conn:
        cursor = conn.cursor()
        field_mappings_json = json.dumps(field_mappings) if field_mappings else None
        cursor.execute(
            """
            INSERT INTO parsing_rules 
            (app_id, name, parser_type, pattern, field_mappings, enabled, priority)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                app_id,
                name,
                parser_type,
                pattern,
                field_mappings_json,
                enabled,
                priority,
            ),
        )
        return cursor.lastrowid


def get_parsing_rule(rule_id: int) -> Optional[Dict[str, Any]]:
    """Get parsing rule by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM parsing_rules WHERE id = ?", (rule_id,))
        row = cursor.fetchone()
        if row:
            rule = dict(row)
            if rule.get("field_mappings"):
                rule["field_mappings"] = json.loads(rule["field_mappings"])
            return rule
        return None


def list_parsing_rules(
    app_id: Optional[int] = None, enabled_only: bool = False
) -> List[Dict[str, Any]]:
    """List parsing rules, optionally filtered by app and enabled status"""
    with get_db() as conn:
        cursor = conn.cursor()

        query = "SELECT * FROM parsing_rules WHERE 1=1"
        params = []

        if app_id is not None:
            query += " AND (app_id = ? OR app_id IS NULL)"
            params.append(app_id)

        if enabled_only:
            query += " AND enabled = 1"

        query += " ORDER BY priority DESC, created_at DESC"

        cursor.execute(query, params)
        rules = []
        for row in cursor.fetchall():
            rule = dict(row)
            if rule.get("field_mappings"):
                rule["field_mappings"] = json.loads(rule["field_mappings"])
            rules.append(rule)
        return rules


def update_parsing_rule(
    rule_id: int,
    name: Optional[str] = None,
    parser_type: Optional[str] = None,
    pattern: Optional[str] = None,
    field_mappings: Optional[Dict[str, Any]] = None,
    enabled: Optional[bool] = None,
    priority: Optional[int] = None,
) -> bool:
    """Update a parsing rule"""
    with get_db() as conn:
        cursor = conn.cursor()

        updates = []
        params = []

        if name is not None:
            updates.append("name = ?")
            params.append(name)

        if parser_type is not None:
            updates.append("parser_type = ?")
            params.append(parser_type)

        if pattern is not None:
            updates.append("pattern = ?")
            params.append(pattern)

        if field_mappings is not None:
            updates.append("field_mappings = ?")
            params.append(json.dumps(field_mappings))

        if enabled is not None:
            updates.append("enabled = ?")
            params.append(enabled)

        if priority is not None:
            updates.append("priority = ?")
            params.append(priority)

        if not updates:
            return False

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(rule_id)

        query = f"UPDATE parsing_rules SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        return cursor.rowcount > 0


def delete_parsing_rule(rule_id: int) -> bool:
    """Delete a parsing rule"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM parsing_rules WHERE id = ?", (rule_id,))
        return cursor.rowcount > 0


def toggle_parsing_rule(rule_id: int) -> bool:
    """Toggle enabled status of a parsing rule"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE parsing_rules 
            SET enabled = NOT enabled, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        """,
            (rule_id,),
        )
        return cursor.rowcount > 0


# Retention Policy Operations
def get_log_levels_for_tier(tier: str) -> List[str]:
    """Get log levels for a priority tier"""
    tier_mapping = {
        "high": ["FATAL", "ERROR"],
        "medium": ["WARN", "INFO"],
        "low": ["DEBUG", "TRACE"],
        "all": ["FATAL", "ERROR", "WARN", "INFO", "DEBUG", "TRACE"],
    }
    return tier_mapping.get(tier, [])


def create_retention_policy(
    app_id: Optional[int],
    priority_tier: str,
    retention_type: str,
    retention_days: Optional[int],
    retention_count: Optional[int],
    enabled: bool = True,
) -> int:
    """Create a new retention policy"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO retention_policies 
            (app_id, priority_tier, retention_type, retention_days, retention_count, enabled)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                app_id,
                priority_tier,
                retention_type,
                retention_days,
                retention_count,
                enabled,
            ),
        )
        return cursor.lastrowid


def get_retention_policy(policy_id: int) -> Optional[Dict[str, Any]]:
    """Get a retention policy by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM retention_policies WHERE id = ?", (policy_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_retention_policies_for_app(
    app_id: Optional[int],
) -> List[Dict[str, Any]]:
    """Get all retention policies for an app (or global if app_id is None)"""
    with get_db() as conn:
        cursor = conn.cursor()
        if app_id is None:
            cursor.execute(
                """
                SELECT * FROM retention_policies 
                WHERE app_id IS NULL 
                ORDER BY 
                    CASE priority_tier 
                        WHEN 'high' THEN 1 
                        WHEN 'medium' THEN 2 
                        WHEN 'low' THEN 3 
                        ELSE 4 
                    END
            """
            )
        else:
            cursor.execute(
                """
                SELECT * FROM retention_policies 
                WHERE app_id = ? 
                ORDER BY 
                    CASE priority_tier 
                        WHEN 'high' THEN 1 
                        WHEN 'medium' THEN 2 
                        WHEN 'low' THEN 3 
                        ELSE 4 
                    END
            """,
                (app_id,),
            )
        return [dict(row) for row in cursor.fetchall()]


def list_all_retention_policies() -> List[Dict[str, Any]]:
    """List all retention policies (global and per-app)"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT rp.*, a.name as app_name 
            FROM retention_policies rp
            LEFT JOIN apps a ON rp.app_id = a.id
            ORDER BY 
                CASE WHEN rp.app_id IS NULL THEN 0 ELSE 1 END,
                a.name,
                CASE rp.priority_tier 
                    WHEN 'high' THEN 1 
                    WHEN 'medium' THEN 2 
                    WHEN 'low' THEN 3 
                    ELSE 4 
                END
        """
        )
        return [dict(row) for row in cursor.fetchall()]


def update_retention_policy(
    policy_id: int,
    retention_type: Optional[str] = None,
    retention_days: Optional[int] = None,
    retention_count: Optional[int] = None,
    enabled: Optional[bool] = None,
) -> bool:
    """Update a retention policy"""
    with get_db() as conn:
        cursor = conn.cursor()
        updates = []
        params = []

        if retention_type is not None:
            updates.append("retention_type = ?")
            params.append(retention_type)
        if retention_days is not None:
            updates.append("retention_days = ?")
            params.append(retention_days)
        if retention_count is not None:
            updates.append("retention_count = ?")
            params.append(retention_count)
        if enabled is not None:
            updates.append("enabled = ?")
            params.append(enabled)

        if not updates:
            return False

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(policy_id)

        query = f"UPDATE retention_policies SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        return cursor.rowcount > 0


def delete_retention_policy(policy_id: int) -> bool:
    """Delete a retention policy"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM retention_policies WHERE id = ?", (policy_id,))
        return cursor.rowcount > 0


# Retention Cleanup Operations
def apply_time_based_retention(policy: Dict[str, Any]) -> int:
    """Apply time-based retention policy and return count of deleted logs"""
    if not policy.get("retention_days"):
        return 0

    with get_db() as conn:
        cursor = conn.cursor()
        levels = get_log_levels_for_tier(policy["priority_tier"])

        # Build query
        if policy["app_id"] is None:
            # Global policy - applies to all apps
            cursor.execute(
                f"""
                DELETE FROM logs 
                WHERE level IN ({",".join("?" * len(levels))})
                AND datetime(timestamp) < datetime('now', '-{policy["retention_days"]} days')
            """,
                levels,
            )
        else:
            # App-specific policy
            cursor.execute(
                f"""
                DELETE FROM logs 
                WHERE app_id = ?
                AND level IN ({",".join("?" * len(levels))})
                AND datetime(timestamp) < datetime('now', '-{policy["retention_days"]} days')
            """,
                [policy["app_id"]] + levels,
            )

        return cursor.rowcount


def apply_count_based_retention(policy: Dict[str, Any]) -> int:
    """Apply count-based retention policy and return count of deleted logs"""
    if not policy.get("retention_count"):
        return 0

    with get_db() as conn:
        cursor = conn.cursor()
        levels = get_log_levels_for_tier(policy["priority_tier"])

        # Get total count of logs matching this policy
        if policy["app_id"] is None:
            cursor.execute(
                f"""
                SELECT COUNT(*) FROM logs 
                WHERE level IN ({",".join("?" * len(levels))})
            """,
                levels,
            )
        else:
            cursor.execute(
                f"""
                SELECT COUNT(*) FROM logs 
                WHERE app_id = ?
                AND level IN ({",".join("?" * len(levels))})
            """,
                [policy["app_id"]] + levels,
            )

        total_count = cursor.fetchone()[0]
        to_delete = total_count - policy["retention_count"]

        if to_delete <= 0:
            return 0

        # Delete oldest logs beyond the retention count
        if policy["app_id"] is None:
            cursor.execute(
                f"""
                DELETE FROM logs 
                WHERE id IN (
                    SELECT id FROM logs 
                    WHERE level IN ({",".join("?" * len(levels))})
                    ORDER BY timestamp ASC
                    LIMIT ?
                )
            """,
                levels + [to_delete],
            )
        else:
            cursor.execute(
                f"""
                DELETE FROM logs 
                WHERE id IN (
                    SELECT id FROM logs 
                    WHERE app_id = ?
                    AND level IN ({",".join("?" * len(levels))})
                    ORDER BY timestamp ASC
                    LIMIT ?
                )
            """,
                [policy["app_id"]] + levels + [to_delete],
            )

        return cursor.rowcount


def apply_retention_policies(app_id: Optional[int] = None) -> Dict[str, int]:
    """
    Apply all active retention policies
    Returns dict with count of deleted logs per policy
    """
    results = {}

    with get_db() as conn:
        cursor = conn.cursor()

        # Get all active policies (global + app-specific if app_id provided)
        if app_id is None:
            # Apply all policies (global + all app-specific)
            cursor.execute(
                """
                SELECT * FROM retention_policies 
                WHERE enabled = 1
                ORDER BY 
                    CASE WHEN app_id IS NULL THEN 0 ELSE 1 END,
                    app_id,
                    CASE priority_tier 
                        WHEN 'high' THEN 1 
                        WHEN 'medium' THEN 2 
                        WHEN 'low' THEN 3 
                        ELSE 4 
                    END
            """
            )
        else:
            # Apply policies for specific app (app-specific overrides global)
            cursor.execute(
                """
                SELECT * FROM retention_policies 
                WHERE enabled = 1
                AND (app_id = ? OR app_id IS NULL)
                ORDER BY 
                    CASE WHEN app_id IS NULL THEN 0 ELSE 1 END,
                    CASE priority_tier 
                        WHEN 'high' THEN 1 
                        WHEN 'medium' THEN 2 
                        WHEN 'low' THEN 3 
                        ELSE 4 
                    END
            """,
                (app_id,),
            )

        policies = [dict(row) for row in cursor.fetchall()]

    # Apply each policy
    for policy in policies:
        key = f"policy_{policy['id']}"
        deleted_count = 0

        try:
            if policy["retention_type"] == "time_based":
                deleted_count = apply_time_based_retention(policy)
            elif policy["retention_type"] == "count_based":
                deleted_count = apply_count_based_retention(policy)

            results[key] = deleted_count
        except Exception as e:
            print(f"Error applying policy {policy['id']}: {e}")
            results[key] = 0

    return results


def preview_retention_cleanup(
    app_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Preview what would be deleted by retention policies (dry run)
    Returns list of preview info per policy
    """
    previews = []

    with get_db() as conn:
        cursor = conn.cursor()

        # Get all active policies
        if app_id is None:
            cursor.execute("SELECT * FROM retention_policies WHERE enabled = 1")
        else:
            cursor.execute(
                """
                SELECT * FROM retention_policies 
                WHERE enabled = 1
                AND (app_id = ? OR app_id IS NULL)
            """,
                (app_id,),
            )

        policies = [dict(row) for row in cursor.fetchall()]

    # For each policy, count what would be deleted
    for policy in policies:
        levels = get_log_levels_for_tier(policy["priority_tier"])

        with get_db() as conn:
            cursor = conn.cursor()

            if policy["retention_type"] == "time_based" and policy["retention_days"]:
                # Count logs that would be deleted
                if policy["app_id"] is None:
                    cursor.execute(
                        f"""
                        SELECT COUNT(*), MIN(timestamp), MAX(timestamp)
                        FROM logs 
                        WHERE level IN ({",".join("?" * len(levels))})
                        AND datetime(timestamp) < datetime('now', '-{policy["retention_days"]} days')
                    """,
                        levels,
                    )
                else:
                    cursor.execute(
                        f"""
                        SELECT COUNT(*), MIN(timestamp), MAX(timestamp)
                        FROM logs 
                        WHERE app_id = ?
                        AND level IN ({",".join("?" * len(levels))})
                        AND datetime(timestamp) < datetime('now', '-{policy["retention_days"]} days')
                    """,
                        [policy["app_id"]] + levels,
                    )

            elif (
                policy["retention_type"] == "count_based" and policy["retention_count"]
            ):
                # Count logs that exceed the retention count
                if policy["app_id"] is None:
                    cursor.execute(
                        f"""
                        SELECT COUNT(*) FROM logs 
                        WHERE level IN ({",".join("?" * len(levels))})
                    """,
                        levels,
                    )
                    total = cursor.fetchone()[0]
                    to_delete = max(0, total - policy["retention_count"])

                    if to_delete > 0:
                        cursor.execute(
                            f"""
                            SELECT {to_delete}, MIN(timestamp), MAX(timestamp)
                            FROM (
                                SELECT timestamp FROM logs 
                                WHERE level IN ({",".join("?" * len(levels))})
                                ORDER BY timestamp ASC
                                LIMIT ?
                            )
                        """,
                            levels + [to_delete],
                        )
                    else:
                        cursor.execute("SELECT 0, NULL, NULL")
                else:
                    cursor.execute(
                        f"""
                        SELECT COUNT(*) FROM logs 
                        WHERE app_id = ?
                        AND level IN ({",".join("?" * len(levels))})
                    """,
                        [policy["app_id"]] + levels,
                    )
                    total = cursor.fetchone()[0]
                    to_delete = max(0, total - policy["retention_count"])

                    if to_delete > 0:
                        cursor.execute(
                            f"""
                            SELECT {to_delete}, MIN(timestamp), MAX(timestamp)
                            FROM (
                                SELECT timestamp FROM logs 
                                WHERE app_id = ?
                                AND level IN ({",".join("?" * len(levels))})
                                ORDER BY timestamp ASC
                                LIMIT ?
                            )
                        """,
                            [policy["app_id"]] + levels + [to_delete],
                        )
                    else:
                        cursor.execute("SELECT 0, NULL, NULL")
            else:
                continue

            row = cursor.fetchone()
            count, oldest, newest = row[0], row[1], row[2]

            # Get app name if applicable
            app_name = None
            if policy["app_id"]:
                app = get_app_by_id(policy["app_id"])
                app_name = app["name"] if app else None

            previews.append(
                {
                    "policy_id": policy["id"],
                    "app_id": policy["app_id"],
                    "app_name": app_name,
                    "priority_tier": policy["priority_tier"],
                    "retention_type": policy["retention_type"],
                    "log_count": count,
                    "oldest_log": oldest,
                    "newest_log": newest,
                }
            )

    return previews


# Retention Run Audit Operations
def create_retention_run(trigger_type: str, user_id: Optional[int] = None) -> int:
    """Create a new retention run record"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO retention_runs 
            (trigger_type, started_at, status, triggered_by_user_id)
            VALUES (?, CURRENT_TIMESTAMP, 'running', ?)
        """,
            (trigger_type, user_id),
        )
        return cursor.lastrowid


def update_retention_run(
    run_id: int,
    status: str,
    logs_deleted: int,
    error_message: Optional[str] = None,
) -> bool:
    """Update a retention run record"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE retention_runs 
            SET completed_at = CURRENT_TIMESTAMP,
                status = ?,
                logs_deleted = ?,
                error_message = ?
            WHERE id = ?
        """,
            (status, logs_deleted, error_message, run_id),
        )
        return cursor.rowcount > 0


def get_retention_run(run_id: int) -> Optional[Dict[str, Any]]:
    """Get a retention run by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT rr.*, wu.username as triggered_by_username
            FROM retention_runs rr
            LEFT JOIN web_users wu ON rr.triggered_by_user_id = wu.id
            WHERE rr.id = ?
        """,
            (run_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None


def list_retention_runs(limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
    """List retention runs with pagination"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT rr.*, wu.username as triggered_by_username
            FROM retention_runs rr
            LEFT JOIN web_users wu ON rr.triggered_by_user_id = wu.id
            ORDER BY rr.started_at DESC
            LIMIT ? OFFSET ?
        """,
            (limit, offset),
        )
        return [dict(row) for row in cursor.fetchall()]
