-- Description: Add email, full_name, role, is_active, and last_login to web_users table

-- up

ALTER TABLE web_users ADD COLUMN email TEXT;
ALTER TABLE web_users ADD COLUMN full_name TEXT;
ALTER TABLE web_users ADD COLUMN role TEXT DEFAULT 'viewer';
ALTER TABLE web_users ADD COLUMN is_active BOOLEAN DEFAULT 1;
ALTER TABLE web_users ADD COLUMN last_login TIMESTAMP;

-- Update existing users to have admin role
UPDATE web_users SET role = 'admin' WHERE role IS NULL OR role = 'viewer';

-- down

-- SQLite doesn't support DROP COLUMN easily without recreating table
-- To rollback, you would need to recreate the web_users table without these columns
-- This is not safe if there's data, so we leave it as a manual process
