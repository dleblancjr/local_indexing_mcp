-- SQLite FTS5 schema for text indexing
-- This script initializes the database schema for the local indexing MCP server

-- Enable FTS5 if not already enabled
PRAGMA compile_options;

-- Set performance pragmas
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

-- Create FTS5 virtual table for searchable content
CREATE VIRTUAL TABLE IF NOT EXISTS documents USING fts5(
    path UNINDEXED,        -- File path (not searchable, just stored)
    content,               -- Full text content (searchable)
    last_modified UNINDEXED, -- ISO timestamp (not searchable)
    tokenize='porter'      -- Use Porter stemming for better search
);

-- Metadata table for change tracking
CREATE TABLE IF NOT EXISTS file_metadata (
    path TEXT PRIMARY KEY,   -- Full file path
    size INTEGER NOT NULL,   -- File size in bytes
    mtime REAL NOT NULL,     -- Modification time (Unix timestamp)
    last_indexed REAL NOT NULL, -- When we last indexed this file
    encoding TEXT,           -- Detected encoding (utf-8, latin-1, etc.)
    error TEXT              -- Error message if indexing failed
);

-- Index for efficient change detection
CREATE INDEX IF NOT EXISTS idx_mtime ON file_metadata(mtime);

-- Index for finding errors
CREATE INDEX IF NOT EXISTS idx_errors ON file_metadata(error) WHERE error IS NOT NULL;

-- View for convenient querying of both tables
CREATE VIEW IF NOT EXISTS indexed_files AS
SELECT 
    fm.path,
    fm.size,
    fm.mtime,
    fm.last_indexed,
    fm.encoding,
    fm.error,
    d.last_modified
FROM file_metadata fm
LEFT JOIN documents d ON fm.path = d.path;

-- Helpful queries commented below:

-- Get all successfully indexed files:
-- SELECT path, size, encoding FROM file_metadata WHERE error IS NULL;

-- Get files with errors:
-- SELECT path, error FROM file_metadata WHERE error IS NOT NULL;

-- Search for content:
-- SELECT path, snippet(documents, 1, '<mark>', '</mark>', '...', 32) as snippet
-- FROM documents WHERE documents MATCH 'search query'
-- ORDER BY bm25(documents) LIMIT 10;

-- Get files that need re-indexing (modified after last index):
-- SELECT path FROM file_metadata WHERE mtime > last_indexed;
