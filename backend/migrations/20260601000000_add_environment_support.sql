-- Description: Add environment support for apps and environment-based retention policies

-- up

-- Add environment column to apps table
ALTER TABLE apps ADD COLUMN environment TEXT DEFAULT 'production';

-- Create index on environment for faster filtering
CREATE INDEX IF NOT EXISTS idx_apps_environment ON apps(environment);

-- Create environment_retention_policies table
CREATE TABLE IF NOT EXISTS environment_retention_policies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    environment TEXT NOT NULL,
    priority_tier TEXT NOT NULL,
    retention_type TEXT NOT NULL,
    retention_days INTEGER,
    retention_count INTEGER,
    enabled BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(environment, priority_tier)
);

-- Create index for efficient querying
CREATE INDEX IF NOT EXISTS idx_env_retention_policies 
ON environment_retention_policies(environment, enabled);

-- Insert default development retention policies (shorter retention)
INSERT INTO environment_retention_policies 
(environment, priority_tier, retention_type, retention_days, enabled)
VALUES 
('development', 'high', 'time_based', 7, 1),      -- Errors: 7 days
('development', 'medium', 'time_based', 3, 1),    -- Info/Warn: 3 days
('development', 'low', 'time_based', 1, 1);       -- Debug: 1 day

-- Insert default staging retention policies (medium retention)
INSERT INTO environment_retention_policies 
(environment, priority_tier, retention_type, retention_days, enabled)
VALUES 
('staging', 'high', 'time_based', 14, 1),         -- Errors: 14 days
('staging', 'medium', 'time_based', 7, 1),        -- Info/Warn: 7 days
('staging', 'low', 'time_based', 3, 1);           -- Debug: 3 days

-- Insert default production retention policies (long retention)
INSERT INTO environment_retention_policies 
(environment, priority_tier, retention_type, retention_days, enabled)
VALUES 
('production', 'high', 'time_based', 90, 1),      -- Errors: 90 days
('production', 'medium', 'time_based', 30, 1),    -- Info/Warn: 30 days
('production', 'low', 'time_based', 7, 1);        -- Debug: 7 days

-- down

-- Drop environment retention policies table
DROP INDEX IF EXISTS idx_env_retention_policies;
DROP TABLE IF EXISTS environment_retention_policies;

-- Drop environment column and index from apps
DROP INDEX IF EXISTS idx_apps_environment;
-- Note: SQLite doesn't support DROP COLUMN easily, would need table recreation
-- For migration rollback, recommend backup before migration
