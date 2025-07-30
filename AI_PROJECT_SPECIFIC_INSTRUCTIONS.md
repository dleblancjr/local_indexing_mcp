## Project-Specific Instructions

### MCP Text Indexing Server Requirements

#### Core Functionality
- **Purpose**: Lightweight text file indexing with full-text search via MCP protocol
- **Python Version**: 3.8+ required
- **Primary Dependencies**: `mcp`, `watchdog` for file monitoring
- **Search Approach**: Keep it simple - use TF-IDF or basic keyword matching instead of heavy ML models

#### Configuration Requirements
```python
# All user-configurable options must be exposed via MCP server initialization
class ServerConfig:
    source_directory: str  # REQUIRED - user must specify
    index_output_directory: str = "./indexes"  # Separate from source
    included_extensions: List[str] = [".txt", ".md", ".rst"]  # User can override
    excluded_extensions: List[str] = []  # User can add to this
    scan_interval_seconds: int = 300  # Default 5 minutes
    use_os_file_events: bool = True  # Prefer OS events, fallback to timestamps
```

#### File Processing Rules
1. **Text Files Only**: Skip binary files automatically. Use file extension + content sampling to detect text files
2. **Self-Exclusion**: Never index the index output directory or any files the server creates
3. **Change Detection**:
   - Primary: Use OS file system events (`watchdog`) when available
   - Fallback: Track file modification timestamps, check every `scan_interval_seconds`
   - Store: `{filepath: {size, mtime, last_indexed}}` for comparison

#### Implementation Patterns
```python
# Simple, focused classes - avoid over-engineering
class FileScanner:
    """Discovers and monitors files for changes."""
    def scan_directory(self, path: Path) -> List[Path]:
        # Simple glob-based scanning
        
class TextIndexer:
    """Processes text files into searchable chunks."""
    def index_file(self, filepath: Path) -> bool:
        # Return False for binary files, True for successful indexing
        # Store processed text in simple JSON or SQLite

class SearchEngine:
    """Provides text search over indexed content."""
    def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        # Use TF-IDF, BM25, or simple keyword matching
        # Store index as JSON files or lightweight SQLite DB
```

#### MCP Tools to Implement
```python
@server.tool()
async def search(query: str, limit: int = 10) -> List[dict]:
    """Search indexed content using text matching."""

@server.tool()
async def get_index_stats() -> dict:
    """Return count of indexed files, last update time, etc."""

@server.tool() 
async def refresh_index(filepath: Optional[str] = None) -> dict:
    """Force re-index of specific file or entire directory."""
```

#### Error Handling Priorities
1. **Graceful Degradation**: Skip problematic files, log warning, continue with others
2. **Clear User Feedback**: Return meaningful error messages via MCP responses
3. **No Silent Failures**: Always log why a file was skipped
4. **Recovery**: Corrupted indexes should be rebuilt, not crash the server

#### Performance Guidelines
- Process files in batches when possible
- Use simple search algorithms (TF-IDF, BM25) that don't require GPU/heavy compute
- Store indexes in JSON files or SQLite for portability
- Limit chunk size to prevent memory issues (e.g., 1000 chars/chunk)
- Use async I/O for file operations
- Set reasonable limits (max file size: 10MB default)

#### Directory Structure
```
project/
├── mcp_server.py      # Main server entry point
├── indexer.py         # Core indexing logic
├── search.py          # Search functionality
├── file_monitor.py    # Change detection
└── indexes/           # Default output directory (git-ignored)
```

#### Lightweight Search Options
- **Option 1**: Use Python's built-in `sqlite3` with FTS5 (Full-Text Search)
- **Option 2**: Simple TF-IDF implementation using only `numpy` and `scipy`
- **Option 3**: Basic keyword matching with ranking based on term frequency
- **Storage**: JSON files for simple indexes, SQLite for larger datasets
- **No heavy dependencies**: Avoid heavy transformer models, FAISS, or GPU-based solutions

#### Key Constraints
- KISS: No complex abstractions for hypothetical future needs
- Single Responsibility: Each module does one thing well
- Fail Fast: Validate configuration at startup
- Defensive: Never trust file paths from user input without validation
- Efficient: Only re-index changed files

#### Testing Focus
- File type detection (text vs binary)
- Change detection accuracy (timestamp precision)
- Index exclusion rules (verify self-exclusion works)
- Path validation (no directory traversal)
- Concurrent file modification handling
- Search relevance (test TF-IDF or chosen algorithm accuracy)