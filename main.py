"""MCP server entry point for local text indexing."""
import asyncio
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP, Context

from src.config import load_config
from src.database import Database
from src.exceptions import ConfigurationError, IndexingError
from src.indexer import FileIndexer
from src.search import SearchEngine
from src.models import IndexStats

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances for lifecycle management
indexer: Optional[FileIndexer] = None
search_engine: Optional[SearchEngine] = None
db: Optional[Database] = None
config = None
background_task = None
_initialized = False
_test_mode = False  # Disable lazy initialization during tests

# Create FastMCP server
mcp = FastMCP("local-indexing-mcp")


async def ensure_initialized() -> None:
    """
    Ensure server is initialized before handling requests.
    
    Checks if the server is already initialized and initializes it if needed.
    Respects test mode to avoid re-initialization during testing.
    
    Args:
        None
        
    Returns:
        None
        
    Raises:
        Exception: If server initialization fails
    """
    global _initialized, _test_mode
    if not _test_mode and not _initialized:
        await initialize_server()
        _initialized = True


@mcp.tool()
async def search(query: str, limit: int = 10) -> str:
    """
    Search indexed content using full-text search.
    
    Args:
        query: Search query string
        limit: Maximum number of results (default: 10)
        
    Returns:
        Search results as formatted string
    """
    await ensure_initialized()
    global search_engine
    
    # Check for proper initialization (especially in test mode)
    if not search_engine:
        return "Error: Server not properly initialized"
    
    try:
        results = search_engine.search(query, limit)
        
        if not results:
            return f"No results found for: {query}"
        
        # Format results
        response = f"Found {len(results)} results for '{query}':\n\n"
        for i, result in enumerate(results, 1):
            response += f"{i}. {result['path']}\n"
            response += f"   Score: {result['score']:.2f}\n"
            response += f"   Modified: {result['last_modified']}\n"
            response += f"   Snippet: {result['snippet']}\n\n"
        
        return response
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return f"Error executing search: {str(e)}"


@mcp.tool()
async def get_index_stats() -> str:
    """
    Get statistics about the current index.
    
    Returns:
        Index statistics as formatted string
    """
    await ensure_initialized()
    global search_engine, db, config
    
    # Check for proper initialization (especially in test mode)
    if not search_engine or not db:
        return "Error: Server not properly initialized"
    
    try:
        doc_count = search_engine.get_document_count()
        
        # Get index size
        db_path = Path(config['index_output_directory']) / "search.db"
        index_size_mb = 0
        if db_path.exists():
            index_size_mb = db_path.stat().st_size / (1024 * 1024)
        
        # Get last scan time from database
        last_scan = "Never"
        errors_count = 0
        
        with db.get_connection() as conn:
            # Get most recent index time
            row = conn.execute(
                "SELECT MAX(last_indexed) as last_scan FROM file_metadata"
            ).fetchone()
            if row and row['last_scan']:
                last_scan = datetime.fromtimestamp(row['last_scan']).isoformat()
            
            # Count errors
            error_row = conn.execute(
                "SELECT COUNT(*) as count FROM file_metadata WHERE error IS NOT NULL"
            ).fetchone()
            errors_count = error_row['count'] if error_row else 0
        
        stats = IndexStats(
            indexed_files=doc_count,
            last_scan=last_scan,
            index_size_mb=round(index_size_mb, 2),
            total_documents=doc_count,
            errors_encountered=errors_count
        )
        
        response = f"""Index Statistics:
- Indexed Files: {stats['indexed_files']}
- Last Scan: {stats['last_scan']}
- Index Size: {stats['index_size_mb']} MB
- Total Documents: {stats['total_documents']}
- Errors Encountered: {stats['errors_encountered']}
"""
        
        return response
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return f"Error getting index stats: {str(e)}"


@mcp.tool()
async def refresh_index(filepath: Optional[str] = None, force: bool = False) -> str:
    """
    Force re-index of specific file or entire directory.
    
    Args:
        filepath: Optional path to specific file to re-index
        force: If True, re-index all files regardless of change detection
        
    Returns:
        Detailed refresh result as formatted string
    """
    await ensure_initialized()
    global indexer
    
    # Check for proper initialization (especially in test mode)
    if not indexer:
        return "Error: Server not properly initialized"
    
    try:
        result = indexer.refresh_index(filepath, force)
        
        # Create detailed response
        status = 'completed' if result['success'] else 'failed'
        mode = 'Force refresh' if force else 'Refresh'
        target = f" of '{filepath}'" if filepath else ''
        
        response = f"""{mode}{target} {status}:
- Duration: {result['duration_seconds']} seconds
- Files Processed: {result['files_processed']}
- Files Added: {result['files_added']}
- Files Updated: {result['files_updated']}
- Files Removed: {result['files_removed']}
- Success: {result['success']}
"""
        
        if result['errors']:
            response += f"- Errors ({len(result['errors'])}):\n"
            for error in result['errors']:
                response += f"  - {error}\n"
        
        return response
        
    except Exception as e:
        logger.error(f"Refresh error: {e}")
        return f"Error executing refresh: {str(e)}"


async def periodic_scan():
    """Background task to periodically scan for changes."""
    global indexer, config
    
    while True:
        try:
            await asyncio.sleep(config['scan_interval_seconds'])
            logger.info("Starting periodic scan...")
            result = indexer.refresh_index()
            logger.info(
                f"Periodic scan complete: {result['files_processed']} files processed "
                f"({result['files_added']} added, {result['files_updated']} updated, "
                f"{result['files_removed']} removed) in {result['duration_seconds']}s"
            )
        except asyncio.CancelledError:
            logger.info("Periodic scan cancelled")
            break
        except Exception as e:
            logger.error(f"Error in periodic scan: {e}")


async def initialize_server():
    """Initialize the server with configuration."""
    global indexer, search_engine, db, config, background_task
    
    try:
        # Load configuration
        config_path = Path("config.json")
        if not config_path.exists():
            # Try example config
            example_path = Path("config.example.json")
            if example_path.exists():
                logger.warning("No config.json found, using config.example.json")
                config_path = example_path
            else:
                raise ConfigurationError(
                    "No configuration file found. "
                    "Please create config.json based on config.example.json"
                )
        
        config = load_config(config_path)
        
        # Initialize database
        db_path = Path(config['index_output_directory']) / "search.db"
        db = Database(db_path)
        
        # Check database integrity
        if not db.rebuild_if_corrupted():
            raise IndexingError("Failed to initialize database")
        
        # Initialize components
        indexer = FileIndexer(config, db)
        search_engine = SearchEngine(db)
        
        # Start background scanning task
        background_task = asyncio.create_task(periodic_scan())
        
        # Do initial scan
        logger.info("Performing initial index scan...")
        result = indexer.refresh_index()
        logger.info(
            f"Initial scan complete: {result['files_processed']} files indexed "
            f"({result['files_added']} added, {result['files_updated']} updated, "
            f"{result['files_removed']} removed) in {result['duration_seconds']}s"
        )
        
    except Exception as e:
        logger.error(f"Failed to initialize server: {e}")
        raise


async def shutdown():
    """Clean shutdown of background tasks."""
    global background_task
    
    if background_task and not background_task.done():
        background_task.cancel()
        try:
            await background_task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    try:
        # Run the FastMCP server with stdio transport
        # Initialization happens lazily when first tool is called
        asyncio.run(mcp.run(transport="stdio"))
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)
