## Project-Specific Instructions

### MCP Text Indexing Server Requirements

#### Core Functionality
- **Purpose**: Lightweight text file indexing with full-text search via MCP protocol
- **Python Version**: 3.8+ required
- **Primary Dependencies**: `mcp` only - everything else uses Python standard library
- **Search Approach**: SQLite FTS5 (Full-Text Search) - built into Python, fast, no external dependencies

#### Configuration Requirements
```python
# All user-configurable options must be exposed via MCP server initialization
from typing import List, TypedDict

class ServerConfig(TypedDict):
    source_directory: str  # REQUIRED - user must specify
    index_output_directory: str  # Default: "./indexes" - Separate from source
    included_extensions: List[str]  # Default: [".txt", ".md", ".rst"]
    excluded_extensions: List[str]  # Default: []
    scan_interval_seconds: int  # Default: 300 (5 minutes)
    max_file_size_mb: float  # Default: 10
```

#### File Processing Rules
1. **Text Files Only**: Skip binary files automatically. Use file extension + content sampling to detect text files
2. **Self-Exclusion**: Never index the index output directory or any files the server creates
3. **Change Detection**:
   - Track file modification timestamps (mtime) and size
   - Check for changes every `scan_interval_seconds`
   - Store: `{filepath: {size, mtime, last_indexed}}` for comparison
   - Only re-index if mtime or size has changed
4. **Recursive Scanning**: Process all subdirectories within source_directory

#### Implementation Patterns
```python
# Simple, focused classes - avoid over-engineering
class FileScanner:
    """Discovers and monitors files for changes using timestamps."""
    def scan_directory(self, path: Path) -> List[Path]:
        # Recursive scanning with os.walk or pathlib
        
    def has_file_changed(self, filepath: Path, last_state: dict) -> bool:
        # Compare current mtime/size with stored values
        
class TextIndexer:
    """Processes text files into SQLite FTS5 index."""
    def index_file(self, filepath: Path) -> bool:
        # Return False for binary files, True for successful indexing
        # Insert into SQLite FTS5 virtual table

class SearchEngine:
    """Provides text search using SQLite FTS5."""
    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        # Use SQLite FTS5 MATCH queries with snippet()
        # Return relevant excerpts with scores
```

#### MCP Tools to Implement
```python
from typing import List, TypedDict

class SearchResult(TypedDict):
    path: str
    snippet: str
    score: float
    last_modified: str

class IndexStats(TypedDict):
    indexed_files: int
    last_scan: str
    index_size_mb: float
    total_documents: int
    errors_encountered: int

class RefreshResult(TypedDict):
    success: bool
    files_processed: int
    errors: List[str]

@server.tool()
async def search(query: str, limit: int = 10) -> List[SearchResult]:
    """Search indexed content using SQLite FTS5."""

@server.tool()
async def get_index_stats() -> IndexStats:
    """Return count of indexed files, last update time, etc."""

@server.tool() 
async def refresh_index(filepath: Optional[str] = None) -> RefreshResult:
    """Force re-index of specific file or entire directory."""
```

#### Error Handling Priorities
1. **Graceful Degradation**: Skip problematic files, log warning, continue with others
2. **Clear User Feedback**: Return meaningful error messages via MCP responses
3. **No Silent Failures**: Always log why a file was skipped
4. **Recovery**: Corrupted indexes should be rebuilt, not crash the server

#### Performance Guidelines
- Process files in batches when possible
- Use SQLite FTS5 virtual tables for efficient full-text search
- Store file metadata in separate SQLite table for change tracking
- Limit file size to prevent memory issues (default: 10MB)
- Use async I/O for file operations where beneficial
- Only re-index files that have changed (compare mtime and size)

#### Directory Structure
```
project/
├── main.py            # MCP server entry point
├── config.py          # Configuration loading and validation
├── indexer.py         # Core indexing logic
├── search.py          # Search functionality using FTS5
├── database.py        # SQLite operations and schema
├── file_utils.py      # File type detection, encoding
├── models.py          # Type definitions and dataclasses
├── exceptions.py      # Custom exceptions
├── config.json        # User configuration
└── indexes/           # Default output directory (git-ignored)
    └── search.db      # SQLite database with FTS5 tables
```

#### SQLite FTS5 Implementation Details
```sql
-- Create FTS5 virtual table for searchable content
CREATE VIRTUAL TABLE documents USING fts5(
    path UNINDEXED,  -- File path (not searchable)
    content,         -- Full text content
    last_modified UNINDEXED,  -- Timestamp (not searchable)
    tokenize='porter'  -- Enable stemming
);

-- Metadata table for change tracking
CREATE TABLE file_metadata (
    path TEXT PRIMARY KEY,
    size INTEGER NOT NULL,
    mtime REAL NOT NULL,
    last_indexed REAL NOT NULL,
    encoding TEXT,
    error TEXT
);

-- Index for efficient change detection
CREATE INDEX idx_mtime ON file_metadata(mtime);
```

#### Search Implementation Notes
- Use `MATCH` queries for FTS5 searches
- Use `snippet()` function to extract relevant text excerpts
- Use `bm25()` ranking function for relevance scoring
- Escape user queries to prevent syntax errors
- Support phrase searches with quotes
- Consider highlighting search terms in results

#### Key Constraints
- KISS: Use SQLite FTS5's built-in features, don't reinvent the wheel
- Single Responsibility: Each module does one thing well
- Fail Fast: Validate configuration at startup
- Defensive: Never trust file paths from user input without validation
- Efficient: Only re-index changed files based on timestamp comparison
- No External Dependencies: Use only Python standard library + mcp

#### Testing Focus
- File type detection (text vs binary)
- Change detection accuracy (timestamp/size comparison)
- Index exclusion rules (verify self-exclusion works)
- Path validation (no directory traversal)
- Unicode and encoding handling
- SQLite FTS5 search relevance
- Configuration loading and validation
- Timestamp precision across different filesystems
- Handling of deleted/moved files
- Database corruption recovery