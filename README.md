# Local Indexing MCP Server

A lightweight MCP (Model Context Protocol) server that provides local text file indexing and full-text search capabilities using SQLite FTS5.

## Features

- 🔍 **Full-text search** using SQLite FTS5 with relevance ranking
- 📁 **Recursive directory scanning** with configurable file filters
- 🔄 **Automatic change detection** using file timestamps
- 📝 **Support for multiple text formats** (txt, md, rst, log, and more)
- 🚀 **Lightweight and fast** - uses only Python standard library + MCP
- 🔒 **Safe and sandboxed** - respects file system boundaries
- 📊 **Index statistics** and error reporting

## Requirements

- Python 3.8 or higher
- MCP (Model Context Protocol) support
- SQLite with FTS5 support (included in Python)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/local-indexing-mcp.git
cd local-indexing-mcp
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e .
```

For development, install with dev dependencies:
```bash
pip install -e ".[dev]"
```

## Configuration

1. Copy the example configuration:
```bash
cp config.example.json config.json
```

2. Edit `config.json` to match your needs:
```json
{
  "source_directory": "/path/to/your/documents",
  "index_output_directory": "./indexes",
  "included_extensions": [".txt", ".md", ".rst", ".py"],
  "excluded_extensions": [".pyc", ".pyo"],
  "scan_interval_seconds": 300,
  "max_file_size_mb": 10
}
```

### Configuration Options

- `source_directory` (required): Path to the directory containing files to index
- `index_output_directory`: Where to store the search index (default: "./indexes")
- `included_extensions`: List of file extensions to include (empty = all text files)
- `excluded_extensions`: List of file extensions to skip
- `scan_interval_seconds`: How often to check for file changes (default: 300)
- `max_file_size_mb`: Maximum file size to index in MB (default: 10)

## Usage

### Starting the Server

Run the MCP server:
```bash
python main.py
```

The server will:
1. Load configuration from `config.json`
2. Perform an initial scan of your source directory
3. Create a search index in the output directory
4. Start listening for MCP tool calls
5. Periodically rescan for changes

### Available MCP Tools

#### 1. Search
Search indexed content using full-text search.

```python
# Tool signature
@mcp.tool()
async def search(query: str, limit: int = 10) -> str:
    """Search indexed content using full-text search."""
```

**Parameters:**
- `query` (required): Search query string
- `limit` (optional): Maximum results to return (default: 10)

**Returns:** List of search results with:
- File path
- Relevance score
- Text snippet with highlighted matches
- Last modified timestamp

#### 2. Get Index Stats
Get statistics about the current index.

```python
# Tool signature
@mcp.tool()
async def get_index_stats() -> str:
    """Get statistics about the current index."""
```

**Returns:**
- Number of indexed files
- Last scan timestamp
- Index size in MB
- Number of errors encountered

#### 3. Refresh Index
Force re-indexing of files.

```python
# Tool signature
@mcp.tool()
async def refresh_index(filepath: Optional[str] = None) -> str:
    """Force re-index of specific file or entire directory."""
```

**Parameters:**
- `filepath` (optional): Specific file to re-index (relative to source directory)

**Returns:**
- Success status
- Number of files processed
- Any errors encountered

## Search Syntax

The search engine supports SQLite FTS5 syntax:

- **Simple search**: `python` - finds documents containing "python"
- **Phrase search**: `"machine learning"` - finds exact phrase
- **Boolean operators**: `python AND tutorial` or `python OR java`
- **Exclusion**: `python NOT java` - finds python but not java
- **Prefix search**: `prog*` - finds "program", "programming", etc.

## Development

### Project Structure

```
local-indexing-mcp/
├── src/
│   ├── __init__.py         # Package initialization
│   ├── config.py           # Configuration management
│   ├── database.py         # SQLite operations
│   ├── exceptions.py       # Custom exceptions
│   ├── file_utils.py       # File handling utilities
│   ├── indexer.py          # Core indexing logic
│   ├── models.py           # Type definitions
│   └── search.py           # Search implementation
├── tests/
│   ├── __init__.py
│   ├── conftest.py         # Pytest fixtures
│   └── test_*.py           # Test files
├── scripts/
│   └── init_db.sql         # Database schema
├── main.py                 # MCP server entry point
├── config.example.json     # Example configuration
├── pyproject.toml          # Project metadata
├── pytest.ini              # Test configuration
└── README.md               # This file
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_indexer.py
```

### Code Quality

```bash
# Format code
black src tests

# Lint code
ruff check src tests

# Type checking
mypy src
```

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and ensure they pass
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Troubleshooting

### Common Issues

1. **"No configuration file found"**
   - Ensure `config.json` exists in the project root
   - Copy from `config.example.json` if needed

2. **"Source directory does not exist"**
   - Check the path in `config.json` is correct
   - Ensure you have read permissions

3. **"Database corruption detected"**
   - The server will attempt to rebuild automatically
   - Delete the index directory to force a full rebuild

4. **Files not being indexed**
   - Check file extensions against included/excluded lists
   - Verify files are under the size limit
   - Check logs for specific error messages

### Logging

The server logs to stdout with timestamps. Log levels:
- INFO: Normal operations (files indexed, searches performed)
- WARNING: Non-critical issues (files skipped, encoding problems)
- ERROR: Critical issues (database errors, configuration problems)

Set environment variable for debug logging:
```bash
export LOG_LEVEL=DEBUG
python main.py
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [MCP (Model Context Protocol)](https://github.com/modelcontextprotocol) using FastMCP
- Uses SQLite FTS5 for full-text search
- Inspired by the need for lightweight, local search solutions
