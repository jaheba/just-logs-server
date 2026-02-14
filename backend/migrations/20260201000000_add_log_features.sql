-- Description: Add parsed fields, tags, and parser_rule_id to logs table

-- up

ALTER TABLE logs ADD COLUMN parsed_fields TEXT;
ALTER TABLE logs ADD COLUMN tags TEXT;
ALTER TABLE logs ADD COLUMN parser_rule_id INTEGER;

-- Add composite index for efficient cleanup queries
CREATE INDEX IF NOT EXISTS idx_logs_app_level_timestamp 
ON logs(app_id, level, timestamp DESC);

-- down

-- SQLite doesn't support DROP COLUMN easily without recreating table
-- To rollback, you would need to recreate the logs table without these columns
-- This is not safe if there's data, so we leave it as a manual process
-- For now, this migration cannot be automatically rolled back
