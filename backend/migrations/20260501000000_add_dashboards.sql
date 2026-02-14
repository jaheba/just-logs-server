-- Description: Add dashboard support with widgets and saved queries

-- up

-- Create dashboards table
CREATE TABLE IF NOT EXISTS dashboards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    owner_id INTEGER NOT NULL,
    is_public BOOLEAN DEFAULT 0,
    layout_config TEXT, -- JSON: grid layout configuration
    refresh_interval INTEGER DEFAULT 60, -- seconds, 0 = no auto-refresh
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES web_users(id) ON DELETE CASCADE
);

-- Create dashboard widgets table
CREATE TABLE IF NOT EXISTS dashboard_widgets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dashboard_id INTEGER NOT NULL,
    widget_type TEXT NOT NULL, -- 'metric', 'chart', 'table', 'log_stream'
    title TEXT NOT NULL,
    position_x INTEGER DEFAULT 0,
    position_y INTEGER DEFAULT 0,
    width INTEGER DEFAULT 4,
    height INTEGER DEFAULT 3,
    config TEXT NOT NULL, -- JSON: widget-specific configuration
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dashboard_id) REFERENCES dashboards(id) ON DELETE CASCADE
);

-- Create saved queries table (for reuse in widgets)
CREATE TABLE IF NOT EXISTS saved_queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    owner_id INTEGER NOT NULL,
    is_public BOOLEAN DEFAULT 0,
    query_config TEXT NOT NULL, -- JSON: filters, aggregations, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES web_users(id) ON DELETE CASCADE
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_dashboards_owner 
ON dashboards(owner_id);

CREATE INDEX IF NOT EXISTS idx_dashboards_public 
ON dashboards(is_public) WHERE is_public = 1;

CREATE INDEX IF NOT EXISTS idx_dashboard_widgets_dashboard 
ON dashboard_widgets(dashboard_id);

CREATE INDEX IF NOT EXISTS idx_saved_queries_owner 
ON saved_queries(owner_id);

CREATE INDEX IF NOT EXISTS idx_saved_queries_public 
ON saved_queries(is_public) WHERE is_public = 1;

-- down

-- Drop all dashboard-related tables and indexes in reverse order
DROP INDEX IF EXISTS idx_saved_queries_public;
DROP INDEX IF EXISTS idx_saved_queries_owner;
DROP TABLE IF EXISTS saved_queries;

DROP INDEX IF EXISTS idx_dashboard_widgets_dashboard;
DROP TABLE IF EXISTS dashboard_widgets;

DROP INDEX IF EXISTS idx_dashboards_public;
DROP INDEX IF EXISTS idx_dashboards_owner;
DROP TABLE IF EXISTS dashboards;
