#!/usr/bin/env python3
"""
Simple MCP client demo for local indexing server.

This demo showcases how to interact with the local indexing MCP server
using the MCP protocol. It demonstrates all available tools: search,
get_index_stats, and refresh_index.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
SERVER_COMMAND = [sys.executable, "../main.py"]
DEFAULT_SEARCH_LIMIT = 5


class MCPClientError(Exception):
    """Custom exception for MCP client-related errors."""
    pass


class LocalIndexingClient:
    """
    Simple MCP client for the local indexing server.
    
    Provides methods to interact with the server's search, statistics,
    and indexing capabilities through the MCP protocol.
    """
    
    def __init__(self) -> None:
        """Initialize the client."""
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self._connected = False
    
    async def connect(self) -> None:
        """
        Connect to the MCP server.
        
        Raises:
            MCPClientError: If connection fails
        """
        try:
            logger.info("Connecting to MCP server...")
            
            # Create server parameters
            server_params = StdioServerParameters(
                command=SERVER_COMMAND[0],
                args=SERVER_COMMAND[1:],
                env=None
            )
            
            # Connect using proper async context manager pattern
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            read_stream, write_stream = stdio_transport
            
            # Create and initialize session
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            await self.session.initialize()
            
            self._connected = True
            logger.info("Successfully connected to MCP server")
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            raise MCPClientError(f"Connection failed: {e}") from e
    
    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        if self._connected:
            try:
                await self.exit_stack.aclose()
                self._connected = False
                self.session = None
                logger.info("Disconnected from MCP server")
            except Exception as e:
                logger.error(f"Error during disconnect: {e}")
    
    def _ensure_connected(self) -> None:
        """
        Ensure client is connected to server.
        
        Raises:
            MCPClientError: If not connected
        """
        if not self._connected or not self.session:
            raise MCPClientError("Client not connected. Call connect() first.")
    
    async def search(self, query: str, limit: int = DEFAULT_SEARCH_LIMIT) -> str:
        """
        Search indexed content.
        
        Args:
            query: Search query string
            limit: Maximum number of results
            
        Returns:
            Search results as formatted string
            
        Raises:
            MCPClientError: If search fails
        """
        self._ensure_connected()
        
        try:
            logger.info(f"Searching for: '{query}' (limit: {limit})")
            
            result = await self.session.call_tool("search", {
                "query": query,
                "limit": limit
            })
            
            if result.isError:
                raise MCPClientError(f"Search failed: {result.content}")
            
            return result.content[0].text if result.content else "No results"
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            raise MCPClientError(f"Search failed: {e}") from e
    
    async def get_index_stats(self) -> str:
        """
        Get index statistics.
        
        Returns:
            Index statistics as formatted string
            
        Raises:
            MCPClientError: If stats retrieval fails
        """
        self._ensure_connected()
        
        try:
            logger.info("Retrieving index statistics...")
            
            result = await self.session.call_tool("get_index_stats", {})
            
            if result.isError:
                raise MCPClientError(f"Stats retrieval failed: {result.content}")
            
            return result.content[0].text if result.content else "No stats available"
            
        except Exception as e:
            logger.error(f"Stats error: {e}")
            raise MCPClientError(f"Stats retrieval failed: {e}") from e
    
    async def refresh_index(
        self, 
        filepath: Optional[str] = None, 
        force: bool = False
    ) -> str:
        """
        Refresh the index.
        
        Args:
            filepath: Optional specific file to refresh
            force: If True, force refresh all files
            
        Returns:
            Refresh results as formatted string
            
        Raises:
            MCPClientError: If refresh fails
        """
        self._ensure_connected()
        
        try:
            args = {"force": force}
            if filepath:
                args["filepath"] = filepath
                
            action = f"Refreshing index for '{filepath}'" if filepath else "Refreshing entire index"
            if force:
                action += " (forced)"
                
            logger.info(action)
            
            result = await self.session.call_tool("refresh_index", args)
            
            if result.isError:
                raise MCPClientError(f"Index refresh failed: {result.content}")
            
            return result.content[0].text if result.content else "Refresh completed"
            
        except Exception as e:
            logger.error(f"Refresh error: {e}")
            raise MCPClientError(f"Index refresh failed: {e}") from e


async def run_demo() -> None:
    """
    Run the MCP client demo.
    
    Demonstrates all available server capabilities with example usage.
    """
    client = LocalIndexingClient()
    
    try:
        # Connect to server
        await client.connect()
        
        print("=== MCP Local Indexing Client Demo ===\n")
        
        # 1. Get index statistics
        print("1. Getting index statistics...")
        stats = await client.get_index_stats()
        print(f"Stats:\n{stats}\n")
        
        # 2. Refresh index to ensure we have recent data
        print("2. Refreshing index...")
        refresh_result = await client.refresh_index()
        print(f"Refresh Result:\n{refresh_result}\n")
        
        # 3. Perform some example searches
        search_queries = [
            "function",
            "class",
            "import",
            "config",
            "error"
        ]
        
        print("3. Performing example searches...")
        for query in search_queries:
            try:
                print(f"\nSearching for '{query}':")
                search_result = await client.search(query, limit=3)
                print(search_result)
            except MCPClientError as e:
                print(f"Search failed: {e}")
        
        # 4. Get final statistics
        print("\n4. Final index statistics...")
        final_stats = await client.get_index_stats()
        print(f"Final Stats:\n{final_stats}")
        
        print("\n=== Demo Complete ===")
        
    except MCPClientError as e:
        logger.error(f"Demo failed: {e}")
        print(f"Demo failed: {e}")
        
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"Unexpected error: {e}")
        
    finally:
        # Ensure cleanup
        await client.disconnect()


async def interactive_demo() -> None:
    """
    Run an interactive demo where users can enter their own commands.
    """
    client = LocalIndexingClient()
    
    try:
        await client.connect()
        
        print("=== Interactive MCP Client Demo ===")
        print("Available commands:")
        print("  search <query> [limit] - Search for content")
        print("  stats                  - Get index statistics")
        print("  refresh [filepath]     - Refresh index")
        print("  refresh --force        - Force refresh entire index")
        print("  help                   - Show this help")
        print("  quit                   - Exit demo")
        print()
        
        while True:
            try:
                command = input("> ").strip()
                
                if not command:
                    continue
                    
                parts = command.split()
                cmd = parts[0].lower()
                
                if cmd == "quit":
                    break
                    
                elif cmd == "help":
                    print("Available commands:")
                    print("  search <query> [limit] - Search for content")
                    print("  stats                  - Get index statistics")
                    print("  refresh [filepath]     - Refresh index")
                    print("  refresh --force        - Force refresh entire index")
                    print("  help                   - Show this help")
                    print("  quit                   - Exit demo")
                    
                elif cmd == "search":
                    if len(parts) < 2:
                        print("Usage: search <query> [limit]")
                        continue
                        
                    query = " ".join(parts[1:])
                    limit = DEFAULT_SEARCH_LIMIT
                    
                    # Check if last part is a number (limit)
                    try:
                        if parts[-1].isdigit():
                            limit = int(parts[-1])
                            query = " ".join(parts[1:-1])
                    except (ValueError, IndexError):
                        pass
                    
                    result = await client.search(query, limit)
                    print(result)
                    
                elif cmd == "stats":
                    result = await client.get_index_stats()
                    print(result)
                    
                elif cmd == "refresh":
                    filepath = None
                    force = False
                    
                    if len(parts) > 1:
                        if parts[1] == "--force":
                            force = True
                        else:
                            filepath = parts[1]
                    
                    result = await client.refresh_index(filepath, force)
                    print(result)
                    
                else:
                    print(f"Unknown command: {cmd}. Type 'help' for available commands.")
                    
            except KeyboardInterrupt:
                print("\nUse 'quit' to exit")
                
            except MCPClientError as e:
                print(f"Error: {e}")
                
            except Exception as e:
                print(f"Unexpected error: {e}")
                logger.error(f"Interactive demo error: {e}")
    
    finally:
        await client.disconnect()


def main() -> None:
    """Main entry point for the demo."""
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        print("Starting interactive demo...")
        asyncio.run(interactive_demo())
    else:
        print("Starting automated demo...")
        asyncio.run(run_demo())


if __name__ == "__main__":
    main()