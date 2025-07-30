#!/usr/bin/env python
"""Diagnostic script to check MCP package version and available imports."""
import sys
import importlib
import pkg_resources
from pathlib import Path


def check_package_version(package_name: str) -> str:
    """
    Get the installed version of a package.
    
    Args:
        package_name: Name of the package to check
        
    Returns:
        Version string or error message
    """
    try:
        version = pkg_resources.get_distribution(package_name).version
        return version
    except Exception as e:
        return f"Error: {str(e)}"


def test_import_patterns():
    """Test various import patterns to find what works."""
    import_tests = [
        # FastMCP pattern (latest)
        ("from mcp.server.fastmcp import FastMCP", 
         "FastMCP import (recommended)"),
        
        ("from mcp.server.fastmcp import FastMCP, Context", 
         "FastMCP with Context"),
        
        # Client imports
        ("from mcp import ClientSession, StdioServerParameters", 
         "Client imports"),
         
        ("from mcp.client.stdio import stdio_client", 
         "Stdio client"),
         
        # Legacy patterns (likely to fail)
        ("from mcp import Server", 
         "Legacy Server import (old API)"),
         
        ("from mcp.server import Server", 
         "Legacy Server from mcp.server"),
    ]
    
    results = []
    
    for import_stmt, description in import_tests:
        try:
            exec(import_stmt, globals())
            results.append(f"✅ {description}: {import_stmt}")
        except ImportError as e:
            results.append(f"❌ {description}: {import_stmt}")
            results.append(f"   Error: {str(e)}")
    
    return results


def main():
    """Run all diagnostics."""
    print("MCP Package Diagnostics for Local Indexing Server")
    print("=" * 60)
    
    # Check version
    print("\n1. Package Version:")
    print("-" * 40)
    version = check_package_version("mcp")
    print(f"MCP version: {version}")
    
    # Test import patterns
    print("\n2. Import Pattern Tests:")
    print("-" * 40)
    
    test_results = test_import_patterns()
    for result in test_results:
        print(result)
    
    # Recommendations
    print("\n3. Migration Notes:")
    print("-" * 40)
    print("✅ This project has been updated to use FastMCP (latest MCP API)")
    print("✅ The old Server class is no longer used")
    print("✅ Tools are now defined with @mcp.tool() decorator")
    print("✅ Server runs with await mcp.run(transport='stdio')")
    
    # Check Python version compatibility
    print(f"\n4. Python Version: {sys.version}")
    print("   Project requires: Python 3.8+")
    if sys.version_info >= (3, 8):
        print("   ✅ Python version compatible")
    else:
        print("   ❌ Python version too old")
    
    # Usage example
    print("\n5. Example Usage with FastMCP:")
    print("-" * 40)
    print("""
from mcp.server.fastmcp import FastMCP

# Create server
mcp = FastMCP("my-server")

# Define tools
@mcp.tool()
async def my_tool(param: str) -> str:
    return f"Processed: {param}"

# Run server
if __name__ == "__main__":
    import asyncio
    asyncio.run(mcp.run(transport="stdio"))
""")


if __name__ == "__main__":
    main()
