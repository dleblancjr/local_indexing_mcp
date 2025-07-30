## Project-Specific Instructions

### MCP Text Indexing Server Requirements

#### Core Functionality
- **Purpose**: Lightweight text file indexing with full-text search via MCP protocol
- **Python Version**: 3.8+ required
- **Primary Dependencies**: `mcp` only - everything else uses Python standard library
- **Search Approach**: SQLite FTS5 (Full-Text Search) - built into Python, fast, no external dependencies
- **Directory Scanning**: Recursive scanning of all subdirectories

#### Configuration
Store configuration in a simple JSON file (`config.json`):
```json
{
  "source_directory": "/path/to/documents",
  "index_output_directory": "./indexes",
  "included_extensions": [".txt", ".md", ".rst"],
  "excluded_extensions": [],
  "scan_interval_seconds": 300,
  "max_file_size_mb": 10
}
```

#### Configuration Validation Rules
- `source_directory`: Must exist and be readable
- `index_output_directory`: Must be writable, created if doesn't exist
- `scan_interval_seconds`: Must be >= 60 (prevent excessive scanning)
- `max_file_size_mb`: Must be > 0 and <= 100 (reasonable limits)
- Extensions: Must start with '.' and be lowercase
- Edge case: source_directory cannot equal index_output_directory

#### File Processing Rules
1. **Text Files Only**: Skip binary files automatically. Use file extension + content sampling to detect text files
2. **Self-Exclusion**: Never index the index output directory or any files the server creates
3. **Change Detection**: Track file modification timestamps, check every `scan_interval_seconds`
   - Store: `{filepath: {size, mtime, last_indexed}}` for comparison
4. **Symlinks**: Skip symbolic links to avoid circular references

#### Text File Encoding
- Try UTF-8 first, fallback to latin-1, then detect with chardet if needed
- Store encoding metadata for each file
- Handle BOM (Byte Order Mark) correctly
- Log encoding issues as warnings, not errors

#### Custom Exceptions
```python
class IndexingError(Exception):
    """Base exception for indexing operations."""
    pass

class FileAccessError(IndexingError):
    """Raised when file cannot be read or accessed."""
    pass

class IndexCorruptionError(IndexingError):
    """Raised when index database is corrupted."""
    pass

class ConfigurationError(IndexingError):
    """Raised when configuration is invalid."""
    pass
```

#### MCP Tools to Implement

```python
from typing import List, Dict, Optional, TypedDict

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
    # Validate query to prevent SQL injection
    # Use parameterized queries
    # Limit result size for resource protection

@server.tool()
async def get_index_stats() -> IndexStats:
    """Return count of indexed files, last update time, etc."""
    # Include error count for monitoring

@server.tool() 
async def refresh_index(filepath: Optional[str] = None) -> RefreshResult:
    """Force re-index of specific file or entire directory."""
    # Validate filepath to prevent directory traversal
    # Return detailed error information
```

#### Error Handling Priorities
1. **Graceful Degradation**: Skip problematic files, log warning, continue with others
2. **Clear User Feedback**: Return meaningful error messages via MCP responses
3. **No Silent Failures**: Always log why a file was skipped
4. **Recovery**: Corrupted indexes should be rebuilt, not crash the server

#### Logging Requirements
- Use Python's logging module with appropriate levels:
  - INFO: File indexed successfully, scan started/completed
  - WARNING: File skipped (too large, binary, access denied)
  - ERROR: Index corruption, configuration errors
  - DEBUG: File change detection details, SQL queries
- Include context: filepath, file size, error details
- Log format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`

#### Performance Guidelines
- Process files in batches when possible
- Store index in SQLite database with FTS5 virtual tables
- Limit file size to prevent memory issues (default: 10MB)
- Use async I/O for file operations where beneficial
- Only re-index files that have changed (compare mtime and size)
- Track indexing speed (files/second)
- Monitor memory usage during large file processing
- Log slow queries (> 100ms)
- Track index size growth over time

#### Database Connection Management
- Use context managers for all database operations
- Implement connection pooling for concurrent access
- Set appropriate SQLite pragmas:
  ```python
  PRAGMA journal_mode=WAL;  # Better concurrency
  PRAGMA synchronous=NORMAL;  # Balance safety/performance
  ```

#### Security Requirements
- Validate all file paths to prevent directory traversal
- Sanitize search queries to prevent SQL injection (use parameters)
- Limit search result size to prevent resource exhaustion
- Consider rate limiting for search operations

#### Suggested Module Structure
```
project/
├── main.py                 # MCP server entry point only
├── config.py              # Configuration loading and validation
├── indexer.py             # File indexing logic
├── search.py              # Search implementation
├── database.py            # SQLite operations and schema
├── file_utils.py          # File type detection, encoding
├── models.py              # Type definitions and dataclasses
├── exceptions.py          # Custom exceptions
├── config.json            # User configuration
├── .gitignore             # Include index directory
└── indexes/               # Default output directory
    └── search.db          # SQLite database with FTS5 tables
```

#### SQLite FTS5 Implementation Notes
- Create virtual table: `CREATE VIRTUAL TABLE documents USING fts5(path, content, last_modified)`
- Store file metadata in a separate table for change tracking
- Use `snippet()` function to return relevant text excerpts in search results
- Enable porter stemming for better search results: `tokenize='porter'`

#### Key Constraints
- KISS: Use SQLite FTS5's built-in features, don't reinvent the wheel
- Single Responsibility: Each function does one thing well
- Fail Fast: Validate configuration at startup
- Defensive: Never trust file paths from user input without validation
- Efficient: Only re-index changed files

#### Testing Focus
- File type detection (text vs binary)
- Change detection accuracy (timestamp precision)
- Index exclusion rules (verify self-exclusion works)
- Path validation (no directory traversal)
- Unicode and encoding handling
- SQLite FTS5 search relevance
- Configuration loading and validation
- Large file handling (at size limit)
- Concurrent file modifications during indexing
- Special characters in filenames/paths
- Symlink handling (follow or skip?)
- Network drive paths (Windows UNC paths)
- Permission changes during operation
- Database recovery from corruption

#### Example .gitignore
```gitignore
# Index files
indexes/
*.db
*.db-wal
*.db-shm

# Logs
*.log

# Config overrides
config.local.json

# Python
__pycache__/
*.py[cod]
*$py.class
.Python
.venv/
venv/
```