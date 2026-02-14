-- Description: Add server_timestamp and rename timestamp to client_timestamp for clarity

-- up

-- Add new server_timestamp column (will be set to current time for existing rows)
ALTER TABLE logs ADD COLUMN server_timestamp TIMESTAMP;

-- Backfill server_timestamp with created_at for existing rows
UPDATE logs SET server_timestamp = created_at WHERE server_timestamp IS NULL;

-- Make server_timestamp NOT NULL after backfilling
-- Note: SQLite doesn't support ALTER COLUMN, so we keep it nullable but enforce in application

-- Create index on server_timestamp for efficient querying
CREATE INDEX IF NOT EXISTS idx_logs_server_timestamp 
ON logs(server_timestamp DESC);

-- Note: We keep 'timestamp' column name for backward compatibility
-- It represents the client timestamp (when the log occurred on the client)
-- Applications should interpret:
--   - timestamp = client_timestamp (when log event occurred)
--   - server_timestamp = when server received the log
--   - created_at = when log was inserted into database (usually same as server_timestamp)

-- down

-- Drop the server_timestamp index and column
DROP INDEX IF EXISTS idx_logs_server_timestamp;
-- Note: SQLite doesn't support DROP COLUMN in older versions
-- For newer SQLite (3.35.0+), uncomment:
-- ALTER TABLE logs DROP COLUMN server_timestamp;
