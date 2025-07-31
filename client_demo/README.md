# Local Indexing MCP Server Demo

This directory contains a complete demonstration of the Local Indexing MCP Server functionality. The demo showcases how to use the MCP server for full-text search, index management, and real-time file indexing.

## Demo Contents

```
client_demo/
├── README.md                    # This file
├── demo_config.json            # Demo configuration 
├── simple_demo.py              # Main demo script
└── sample_documents/           # Sample files to index
    ├── README.md               # Demo documentation
    ├── python_tutorial.txt     # Python programming content
    ├── machine_learning.md     # ML concepts and algorithms
    └── sample_code.py          # Example Python code
```

## What the Demo Shows

### 🔍 Search Functionality
- Full-text search across multiple file types (.txt, .md, .py)
- Relevance scoring and result ranking
- Search result snippets with context
- Support for various search queries

### 📊 Index Statistics
- Number of indexed files
- Index size and performance metrics
- Last scan timestamp
- Error reporting and monitoring

### 🔄 Dynamic Indexing
- Automatic file change detection
- Manual index refresh capabilities
- Real-time indexing of new files
- Cleanup and maintenance operations

### 📝 Real-time Updates
- Creation of new test files
- Immediate indexing and search
- Demonstration of live file monitoring

## Prerequisites

1. **Python 3.8+** with required dependencies installed:
   ```bash
   pip install -e .
   ```

2. **Project structure** - Run from the project root directory where `main.py` is located

3. **Demo files** - The demo will use the pre-created sample documents

## Running the Demo

### Option 1: Simple Direct Demo (Recommended)

From the project root directory, run:

```bash
python client_demo/simple_demo.py
```

This demo directly imports and uses the MCP server components, avoiding protocol complexity.

### Option 2: MCP Inspector (Professional Testing)

For a more thorough test using the official MCP development tools:

```bash
python client_demo/mcp_inspector_demo.py
```

This launches the MCP Inspector, which provides a web-based interface for testing all MCP functionality. This is the recommended way to test MCP servers during development.

### Option 3: Manual MCP Inspector

If you have the MCP SDK installed (`pip install mcp`):

```bash
# From the project root directory
python -m mcp dev main.py
```

This opens the MCP Inspector in your browser for interactive testing.

### What You'll See

The demo will automatically:

1. **Initialize** - Check configuration and sample files
2. **Show Index Stats** - Display current index information
3. **Demonstrate Search** - Run several search queries:
   - `"python"` - Find Python-related content
   - `"machine learning"` - Find ML concepts
   - `"function"` - Find programming constructs
   - `"class"` - Find OOP content  
   - `"fibonacci"` - Find specific algorithms
4. **Refresh Index** - Force a complete re-indexing
5. **Dynamic Test** - Create, index, and search a new file
6. **Cleanup** - Remove test files

### Expected Output

```
============================================================
🚀 LOCAL INDEXING MCP SERVER DEMO
============================================================

📊 === INDEX STATISTICS ===
--------------------------------------------------
Index Statistics:
- Indexed Files: 4
- Last Scan: 2024-01-15T10:30:45
- Index Size: 0.15 MB
- Total Documents: 4
- Errors Encountered: 0

🔍 === SEARCH DEMONSTRATION ===

🔍 Searching for: 'python'
--------------------------------------------------
Found 3 results for 'python':

1. client_demo/sample_documents/python_tutorial.txt
   Score: 2.85
   Modified: 2024-01-15T10:25:30
   Snippet: Python Programming Tutorial...

[... more results ...]
```

## Customizing the Demo

### Modify Configuration

Edit `client_demo/demo_config.json` to change:

```json
{
  "source_directory": "./client_demo/sample_documents",
  "index_output_directory": "./client_demo/indexes",
  "included_extensions": [".txt", ".md", ".py"],
  "excluded_extensions": [".pyc", ".pyo"],
  "scan_interval_seconds": 300,
  "max_file_size_mb": 10
}
```

### Add Your Own Files

1. Add files to `client_demo/sample_documents/`
2. Run the demo to see them indexed and searchable
3. Try different file types and content

### Test Different Searches

Modify the search queries in `simple_demo.py`:

```python
search_queries = [
    "your custom search",
    "another query",
    '"exact phrase search"',
    'boolean AND queries'
]
```

## Understanding the Results

### Search Results Format

Each search result includes:
- **File Path**: Location of the matching file
- **Score**: Relevance score (higher = more relevant)
- **Modified**: Last modification timestamp
- **Snippet**: Context around the matching text

### Index Statistics Meaning

- **Indexed Files**: Number of successfully indexed documents
- **Last Scan**: When the index was last updated
- **Index Size**: Storage space used by the search index
- **Errors**: Number of files that couldn't be indexed

## Troubleshooting

### Common Issues

1. **"Demo configuration not found"**
   - Ensure you're running from the project root
   - Check that `client_demo/demo_config.json` exists

2. **"Sample documents not found"**
   - Verify `client_demo/sample_documents/` exists and contains files
   - Run the demo setup if files are missing

3. **"Error running MCP server"**
   - Check that dependencies are installed: `pip install -e .`
   - Ensure `main.py` is accessible from current directory
   - Verify Python version is 3.8+

4. **No search results**
   - Check that files were successfully indexed
   - Try simpler search terms
   - Verify file extensions match configuration

### Debug Mode

For more detailed output, you can modify the demo script to include debug information or run the MCP server separately:

```bash
# Run server separately for debugging
python main.py

# In another terminal, test individual commands
python -c "import asyncio; from client_demo.simple_demo import run_mcp_server_command; print(asyncio.run(run_mcp_server_command('get_index_stats')))"
```

## Next Steps

After running the demo:

1. **Explore the codebase** - Look at `main.py` and `src/` to understand implementation
2. **Try your own data** - Point the config to your documents directory
3. **Integrate with applications** - Use the MCP tools in your own projects
4. **Experiment with search** - Try complex queries, boolean operators, phrase searches
5. **Monitor performance** - Watch index statistics as you add more files

## Advanced Usage

### Custom MCP Client

The demo uses a simple subprocess approach. For production use, consider implementing a proper MCP client using the MCP SDK:

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# More sophisticated client implementation
async def create_mcp_client():
    server_params = StdioServerParameters(
        command="python", 
        args=["main.py"]
    )
    
    async with stdio_client(server_params) as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            # Use session.call_tool() for tool calls
            pass
```

### Integration Examples

The MCP server can be integrated into:
- **IDEs and editors** - For code search functionality
- **Documentation systems** - For content discovery
- **Knowledge management** - For information retrieval
- **Content management** - For document search

## Support

For issues or questions:
1. Check the main project README
2. Review the source code documentation
3. Create an issue in the project repository
4. Refer to MCP documentation for protocol details