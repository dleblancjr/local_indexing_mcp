# MCP Local Indexing Client Demo

A simple demonstration client for the local indexing MCP server. This demo showcases how to communicate with the MCP server using the Model Context Protocol to perform text indexing and search operations.

## Features

- **Search**: Full-text search across indexed content
- **Index Statistics**: Get detailed information about the current index
- **Index Refresh**: Trigger manual re-indexing of files
- **Interactive Mode**: Command-line interface for real-time interaction
- **Automated Demo**: Pre-built demonstration of all features

## Prerequisites

1. **Python 3.10+**: Ensure you have Python 3.10 or later installed
2. **MCP Server**: The local indexing MCP server must be available in the parent directory
3. **Dependencies**: Install required packages (see Installation section)

## Installation

1. **Install dependencies**:
   ```bash
   pip install mcp>=1.0.0
   ```

2. **Ensure server is configured**:
   - Make sure `../main.py` exists (the MCP server)
   - Verify `../config.json` is properly configured
   - The server should have indexed content to search

## Usage

### Automated Demo

Run the pre-built demonstration that showcases all features:

```bash
cd client_demo
python simple_demo.py
```

This will:
1. Connect to the MCP server
2. Display current index statistics
3. Refresh the index
4. Perform several example searches
5. Show final statistics

### Interactive Mode

For hands-on exploration, use interactive mode:

```bash
cd client_demo
python simple_demo.py --interactive
```

Available commands in interactive mode:

- `search <query> [limit]` - Search for content (optional limit, default: 5)
- `stats` - Get current index statistics
- `refresh [filepath]` - Refresh index (optionally for specific file)
- `refresh --force` - Force refresh entire index
- `help` - Show available commands
- `quit` - Exit the demo

### Example Interactive Session

```
> stats
Index Statistics:
- Indexed Files: 42
- Last Scan: 2024-01-15T10:30:00
- Index Size: 2.3 MB
- Total Documents: 42
- Errors Encountered: 0

> search function 3
Found 3 results for 'function':

1. src/indexer.py
   Score: 0.95
   Modified: 2024-01-15T09:15:00
   Snippet: def index_file(self, filepath: Path) -> bool: ...

2. src/search.py
   Score: 0.87
   Modified: 2024-01-15T09:10:00
   Snippet: def search(self, query: str, limit: int = 10) -> List[Dict]: ...

3. main.py
   Score: 0.82
   Modified: 2024-01-15T09:00:00
   Snippet: async def search(query: str, limit: int = 10) -> str: ...

> refresh
Refresh completed:
- Duration: 1.2 seconds
- Files Processed: 5
- Files Added: 0
- Files Updated: 2
- Files Removed: 0
- Success: True

> quit
```

## Code Structure

### `simple_demo.py`

The main demo file contains:

- **`LocalIndexingClient`**: MCP client class that handles server communication
- **`run_demo()`**: Automated demonstration function
- **`interactive_demo()`**: Interactive command-line interface
- **Error handling**: Comprehensive error management with custom exceptions

### Key Features

1. **Clean Architecture**: Follows SOLID principles with clear separation of concerns
2. **Type Safety**: Full type hints throughout the codebase
3. **Error Handling**: Custom exceptions with detailed error messages
4. **Logging**: Comprehensive logging for debugging and monitoring
5. **Documentation**: Detailed docstrings following Google style

## Error Handling

The demo includes robust error handling for common scenarios:

- **Connection failures**: Server not available or misconfigured
- **Tool execution errors**: Server-side errors during tool calls
- **Invalid inputs**: Malformed queries or parameters
- **Network issues**: Communication problems with the server

All errors are logged with context and provide user-friendly messages.

## Troubleshooting

### Common Issues

1. **"Client not connected"**
   - Ensure the MCP server is running and accessible
   - Check that `../main.py` exists and is executable
   - Verify server configuration in `../config.json`

2. **"Connection failed"**
   - Make sure you're running from the `client_demo` directory
   - Check that the server has proper permissions
   - Review server logs for startup errors

3. **"No results found"**
   - Verify the index contains data (run `refresh --force`)
   - Check that the search directory has indexable files
   - Try broader search terms

4. **"Tool execution failed"**
   - Check server logs for detailed error information
   - Ensure proper file permissions for indexing
   - Verify disk space for index storage

### Getting Help

1. **Check logs**: Both client and server provide detailed logging
2. **Review server status**: Use `stats` command to check server health
3. **Force refresh**: Try `refresh --force` to rebuild the index
4. **Server configuration**: Verify `../config.json` settings

## Development

### Adding New Features

To extend the demo:

1. **Add new methods** to `LocalIndexingClient` for additional server tools
2. **Update interactive commands** in `interactive_demo()` function
3. **Follow coding standards** from `../CODING_INSTRUCTIONS.md`
4. **Add error handling** for new functionality
5. **Update documentation** with new features

### Code Quality

The demo follows the project's coding standards:

- Functions under 20 lines
- Comprehensive type hints
- Detailed docstrings
- Specific exception handling
- KISS principle adherence

## License

This demo is part of the local-indexing-mcp project and follows the same licensing terms.