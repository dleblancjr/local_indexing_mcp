#!/usr/bin/env python3
"""
Simple MCP Demo for Local Indexing MCP Server

This demo shows the Local Indexing MCP Server functionality by directly
importing and using the server components, avoiding complex protocol issues.

To run this demo:
1. Make sure you're in the project root directory
2. Run: python client_demo/simple_demo.py
"""

import asyncio
import logging
import sys
import traceback
from pathlib import Path
from typing import Any, List

# Add client_demo to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from config_manager import ConfigError, setup_demo_config, restore_config, validate_demo_paths

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_SEARCH_LIMIT = 3
SEARCH_QUERIES = [
    "python",
    "machine learning", 
    "function",
    "class",
    "fibonacci"
]


class DemoError(Exception):
    """Custom exception for demo-related errors."""
    pass


async def initialize_mcp_server() -> None:
    """
    Initialize the MCP server for demo use.
    
    Raises:
        DemoError: If server initialization fails
    """
    try:
        from main import initialize_server
        import main
        
        # Set test mode to avoid background tasks
        main._test_mode = True
        
        # Initialize the server
        await initialize_server()
        logger.info("MCP server initialized successfully")
        
    except ImportError as e:
        logger.error(f"Failed to import MCP server components: {e}")
        raise DemoError("Cannot import MCP server - ensure you're in project root") from e
    except Exception as e:
        logger.error(f"Server initialization failed: {e}")
        raise DemoError(f"Server initialization failed: {e}") from e


async def call_search_tool(query: str, limit: int = DEFAULT_SEARCH_LIMIT) -> str:
    """
    Call the search tool with specified parameters.
    
    Args:
        query: Search query string
        limit: Maximum number of results to return
        
    Returns:
        Search results as formatted string
        
    Raises:
        DemoError: If search operation fails
    """
    try:
        from main import search
        return await search(query, limit)
    except Exception as e:
        logger.error(f"Search failed for query '{query}': {e}")
        raise DemoError(f"Search operation failed: {e}") from e


async def call_stats_tool() -> str:
    """
    Call the index statistics tool.
    
    Returns:
        Index statistics as formatted string
        
    Raises:
        DemoError: If stats operation fails
    """
    try:
        from main import get_index_stats
        return await get_index_stats()
    except Exception as e:
        logger.error(f"Stats operation failed: {e}")
        raise DemoError(f"Stats operation failed: {e}") from e


async def call_refresh_tool(filepath: str = None, force: bool = False) -> str:
    """
    Call the index refresh tool.
    
    Args:
        filepath: Optional specific file to refresh
        force: Whether to force refresh all files
        
    Returns:
        Refresh results as formatted string
        
    Raises:
        DemoError: If refresh operation fails
    """
    try:
        from main import refresh_index
        return await refresh_index(filepath, force)
    except Exception as e:
        logger.error(f"Refresh operation failed: {e}")
        raise DemoError(f"Refresh operation failed: {e}") from e


async def demonstrate_search() -> None:
    """
    Demonstrate the search functionality with various queries.
    
    Raises:
        DemoError: If search demonstration fails
    """
    print("🔍 === SEARCH DEMONSTRATION ===")
    
    for query in SEARCH_QUERIES:
        print(f"\n🔍 Searching for: '{query}'")
        print("-" * 50)
        try:
            result = await call_search_tool(query, DEFAULT_SEARCH_LIMIT)
            print(result)
        except DemoError as e:
            print(f"❌ Search failed: {e}")


async def demonstrate_index_stats() -> None:
    """
    Demonstrate getting index statistics.
    
    Raises:
        DemoError: If stats demonstration fails
    """
    print("\n📊 === INDEX STATISTICS ===")
    print("-" * 50)
    try:
        result = await call_stats_tool()
        print(result)
    except DemoError as e:
        print(f"❌ Stats failed: {e}")


async def demonstrate_refresh_index() -> None:
    """
    Demonstrate refreshing the index.
    
    Raises:
        DemoError: If refresh demonstration fails
    """
    print("\n🔄 === INDEX REFRESH ===")
    print("-" * 50)
    try:
        result = await call_refresh_tool(force=True)
        print(result)
    except DemoError as e:
        print(f"❌ Refresh failed: {e}")


async def create_test_file_and_search() -> None:
    """
    Create a test file, index it, and search for unique content.
    
    Demonstrates real-time indexing capabilities by creating a temporary
    file with unique keywords, indexing it, and searching for the content.
    """
    print("\n📝 === DYNAMIC INDEXING TEST ===")
    
    test_file = Path("client_demo/sample_documents/dynamic_test.txt")
    test_content = """
This is a dynamically created test file for the MCP demo.
It contains unique keywords like: UNIQUEWORD123 and TESTCONTENT456.
This file was created to demonstrate real-time indexing capabilities.
"""
    
    try:
        print("Creating new test file...")
        test_file.write_text(test_content)
        logger.info(f"Created test file: {test_file}")
        
        print("Refreshing index to include new file...")
        refresh_result = await call_refresh_tool()
        print(refresh_result)
        
        print("\nSearching for unique keyword from new file...")
        search_result = await call_search_tool("UNIQUEWORD123", limit=2)
        print(search_result)
        
    except DemoError as e:
        print(f"❌ Dynamic indexing test failed: {e}")
        logger.error(f"Dynamic indexing test failed: {e}")
    except (OSError, IOError) as e:
        print(f"❌ File operation failed: {e}")
        logger.error(f"File operation failed: {e}")
    finally:
        # Clean up test file
        if test_file.exists():
            try:
                test_file.unlink()
                print(f"\n✅ Cleaned up test file: {test_file}")
                logger.info(f"Cleaned up test file: {test_file}")
            except OSError as e:
                print(f"⚠️  Failed to clean up test file: {e}")
                logger.warning(f"Failed to clean up test file: {e}")


def print_welcome() -> None:
    """Print welcome message and demo information."""
    welcome_lines = [
        "=" * 60,
        "🚀 LOCAL INDEXING MCP SERVER DEMO", 
        "=" * 60,
        "",
        "This demo showcases the Local Indexing MCP Server functionality:",
        "• Full-text search across indexed documents",
        "• Index statistics and monitoring", 
        "• Dynamic index refresh capabilities",
        "• Real-time file indexing",
        "",
        "Demo files located in: client_demo/sample_documents/",
        "Configuration: client_demo/demo_config.json",
        ""
    ]
    print("\n".join(welcome_lines))


def print_conclusion() -> None:
    """Print conclusion message with demo summary and next steps."""
    conclusion_lines = [
        "\n" + "=" * 60,
        "✅ DEMO COMPLETED SUCCESSFULLY!",
        "=" * 60,
        "",
        "What you've seen:",
        "• Search functionality across multiple file types",
        "• Index statistics and performance metrics",
        "• Automatic file change detection and indexing", 
        "• Real-time search of newly added content",
        "",
        "Next steps:",
        "• Modify client_demo/demo_config.json to index your own files",
        "• Add more documents to client_demo/sample_documents/",
        "• Integrate the MCP server into your own applications",
        "• Explore advanced search syntax (boolean operators, phrases)",
        ""
    ]
    print("\n".join(conclusion_lines))


async def run_demo_sequence() -> None:
    """
    Run the complete demo sequence.
    
    Raises:
        DemoError: If any demo step fails
    """
    await demonstrate_index_stats()
    await demonstrate_search()
    await demonstrate_refresh_index()
    await create_test_file_and_search()


async def main() -> None:
    """
    Main demo function with comprehensive error handling.
    
    Sets up configuration, validates environment, runs demo sequence,
    and ensures proper cleanup.
    """
    print_welcome()
    
    config_set = False
    try:
        # Validate demo environment
        success, message = validate_demo_paths()
        if not success:
            print(f"❌ Environment validation failed: {message}")
            return
        
        # Set up demo configuration
        config_set = setup_demo_config()
        if not config_set:
            print("❌ Demo configuration setup failed!")
            print("Please ensure client_demo/demo_config.json exists.")
            return
        
        # Add current directory to Python path for imports
        current_dir = Path.cwd()
        if str(current_dir) not in sys.path:
            sys.path.insert(0, str(current_dir))
        
        # Initialize server
        await initialize_mcp_server()
        
        # Run demo sequence
        await run_demo_sequence()
        
        print_conclusion()
        
    except KeyboardInterrupt:
        print("\n⚠️  Demo interrupted by user")
        logger.info("Demo interrupted by user")
    except (ConfigError, DemoError) as e:
        print(f"\n❌ Demo failed: {e}")
        logger.error(f"Demo failed: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        logger.error(f"Unexpected error: {e}")
        print("\nFull error traceback:")
        traceback.print_exc()
        print("\nPlease check that:")
        print("• Python dependencies are installed (pip install -e .)")
        print("• You're running from the project root directory")
        print("• The MCP server main.py file is accessible")
    finally:
        # Restore original configuration
        if config_set:
            try:
                restore_config()
            except ConfigError as e:
                print(f"⚠️  Failed to restore configuration: {e}")
                logger.warning(f"Failed to restore configuration: {e}")


if __name__ == "__main__":
    asyncio.run(main())