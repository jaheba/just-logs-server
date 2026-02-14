-- Description: Initial database schema for just-logging

-- up

-- Create apps table
CREATE TABLE IF NOT EXISTS apps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create api_keys table
CREATE TABLE IF NOT EXISTS api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    app_id INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (app_id) REFERENCES apps(id)
);

-- Create index on api_keys.key for fast lookups
CREATE INDEX IF NOT EXISTS idx_api_keys_key 
ON api_keys(key) WHERE is_active = 1;

-- Create api_key_tags table
CREATE TABLE IF NOT EXISTS api_key_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_key_id INTEGER NOT NULL,
    tag_key TEXT NOT NULL,
    tag_value TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (api_key_id) REFERENCES api_keys(id) ON DELETE CASCADE,
    UNIQUE(api_key_id, tag_key)
);

-- Create indexes on api_key_tags
CREATE INDEX IF NOT EXISTS idx_api_key_tags_key_id 
ON api_key_tags(api_key_id);

CREATE INDEX IF NOT EXISTS idx_api_key_tags_key 
ON api_key_tags(tag_key);

-- Create logs table
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    app_id INTEGER NOT NULL,
    level TEXT NOT NULL,
    message TEXT NOT NULL,
    structured_data TEXT,
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (app_id) REFERENCES apps(id)
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_logs_timestamp 
ON logs(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_logs_app_id 
ON logs(app_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_logs_level 
ON logs(level, timestamp DESC);

-- Create web_users table
CREATE TABLE IF NOT EXISTS web_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create parsing_rules table
CREATE TABLE IF NOT EXISTS parsing_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    app_id INTEGER,
    name TEXT NOT NULL,
    parser_type TEXT NOT NULL,
    pattern TEXT NOT NULL,
    field_mappings TEXT,
    enabled BOOLEAN DEFAULT 1,
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (app_id) REFERENCES apps(id)
);

-- Create index on parsing_rules for efficient querying
CREATE INDEX IF NOT EXISTS idx_parsing_rules_app_id 
ON parsing_rules(app_id, enabled, priority DESC);

-- Create retention_policies table
CREATE TABLE IF NOT EXISTS retention_policies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    app_id INTEGER,
    priority_tier TEXT NOT NULL,
    retention_type TEXT NOT NULL,
    retention_days INTEGER,
    retention_count INTEGER,
    enabled BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (app_id) REFERENCES apps(id) ON DELETE CASCADE,
    UNIQUE(app_id, priority_tier)
);

-- Create index on retention_policies for efficient querying
CREATE INDEX IF NOT EXISTS idx_retention_policies_app_id 
ON retention_policies(app_id, enabled);

-- Create retention_runs table (audit log)
CREATE TABLE IF NOT EXISTS retention_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trigger_type TEXT NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    status TEXT NOT NULL,
    logs_deleted INTEGER DEFAULT 0,
    error_message TEXT,
    triggered_by_user_id INTEGER,
    FOREIGN KEY (triggered_by_user_id) REFERENCES web_users(id)
);

-- Create index on retention_runs for efficient querying
CREATE INDEX IF NOT EXISTS idx_retention_runs_started_at 
ON retention_runs(started_at DESC);

-- down

-- Drop all tables in reverse order (respect foreign keys)
DROP INDEX IF EXISTS idx_retention_runs_started_at;
DROP TABLE IF EXISTS retention_runs;

DROP INDEX IF EXISTS idx_retention_policies_app_id;
DROP TABLE IF EXISTS retention_policies;

DROP INDEX IF EXISTS idx_parsing_rules_app_id;
DROP TABLE IF EXISTS parsing_rules;

DROP TABLE IF EXISTS web_users;

DROP INDEX IF EXISTS idx_logs_level;
DROP INDEX IF EXISTS idx_logs_app_id;
DROP INDEX IF EXISTS idx_logs_timestamp;
DROP TABLE IF EXISTS logs;

DROP INDEX IF EXISTS idx_api_key_tags_key;
DROP INDEX IF EXISTS idx_api_key_tags_key_id;
DROP TABLE IF EXISTS api_key_tags;

DROP INDEX IF EXISTS idx_api_keys_key;
DROP TABLE IF EXISTS api_keys;

DROP TABLE IF EXISTS apps;
