#!/usr/bin/env python3
"""
MCP Inspector Demo for Local Indexing MCP Server

This script shows how to test the MCP server using the official MCP Inspector tool.
This is the recommended way to test MCP servers during development.

Prerequisites:
- MCP Python SDK installed: pip install mcp
- Project dependencies installed: pip install -e .

Usage:
1. From the project root directory, run: python client_demo/mcp_inspector_demo.py
2. This will launch the MCP Inspector in your browser
3. The inspector provides a web UI to test all MCP functionality
"""

import subprocess
import sys
import logging
from pathlib import Path
from typing import Tuple

# Add client_demo to path for imports  
sys.path.insert(0, str(Path(__file__).parent))
from config_manager import ConfigError, setup_demo_config, restore_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class InspectorError(Exception):
    """Custom exception for MCP Inspector demo errors."""
    pass


def check_dependencies() -> bool:
    """
    Check that required dependencies are available.
    
    Returns:
        True if all dependencies are available, False otherwise
    """
    try:
        import mcp
        print("✅ MCP SDK is available")
        logger.info("MCP SDK dependency check passed")
        return True
    except ImportError:
        print("❌ MCP SDK not found. Install with: pip install mcp")
        logger.error("MCP SDK not found")
        return False


def launch_mcp_inspector() -> bool:
    """
    Launch the MCP Inspector for testing the server.
    
    Returns:
        True if inspector launched successfully, False otherwise
        
    Raises:
        InspectorError: If inspector launch fails
    """
    try:
        print("\n🚀 Launching MCP Inspector...")
        print("This will open the MCP Inspector in your browser.")
        print("The inspector provides a web UI to test all MCP functionality.")
        print("\nStarting server with MCP Inspector...")
        
        # Use the mcp command to run the inspector
        cmd = [sys.executable, "-m", "mcp", "dev", "main.py"]
        
        print(f"Running: {' '.join(cmd)}")
        print("\nPress Ctrl+C to stop the server when done testing...")
        
        logger.info(f"Launching MCP Inspector with command: {' '.join(cmd)}")
        
        # Run the inspector
        process = subprocess.run(cmd, cwd=Path.cwd())
        success = process.returncode == 0
        
        if success:
            logger.info("MCP Inspector completed successfully")
        else:
            logger.error(f"MCP Inspector failed with return code: {process.returncode}")
            
        return success
        
    except KeyboardInterrupt:
        print("\n✅ MCP Inspector stopped by user")
        logger.info("MCP Inspector stopped by user")
        return True
    except (OSError, subprocess.SubprocessError) as e:
        error_msg = f"Failed to launch MCP Inspector: {e}"
        print(f"❌ {error_msg}")
        logger.error(error_msg)
        raise InspectorError(error_msg) from e


def print_instructions():
    """Print instructions for using the MCP Inspector."""
    print("=" * 70)
    print("🔍 MCP INSPECTOR DEMO")
    print("=" * 70)
    print()
    print("The MCP Inspector is the official tool for testing MCP servers.")
    print("It provides a web-based interface to:")
    print()
    print("🔧 Test all server tools:")
    print("   • search - Full-text search across indexed documents")
    print("   • get_index_stats - View index statistics and status")
    print("   • refresh_index - Force re-indexing of files")
    print()
    print("📋 Explore server capabilities:")
    print("   • View available tools and their schemas")
    print("   • Test tool calls with different parameters")
    print("   • See real-time server responses")
    print()
    print("📁 Test with demo content:")
    print("   • Sample documents are in client_demo/sample_documents/")
    print("   • Try searches like: 'python', 'function', 'machine learning'")
    print("   • View index statistics to see indexed file count")
    print()


def print_demo_examples():
    """Print examples of what to try in the MCP Inspector."""
    print("\n" + "=" * 70)
    print("🎯 WHAT TO TRY IN THE MCP INSPECTOR")
    print("=" * 70)
    print()
    print("1. 📊 GET INDEX STATS")
    print("   Tool: get_index_stats")
    print("   Parameters: (none)")
    print("   Expected: Shows number of indexed files, last scan time, etc.")
    print()
    print("2. 🔍 SEARCH FOR CONTENT")
    print("   Tool: search")
    print("   Parameters:")
    print("   • query: 'python'")
    print("   • limit: 5")
    print("   Expected: Finds Python-related content with scores and snippets")
    print()
    print("3. 🔍 TRY DIFFERENT SEARCHES")
    print("   • 'machine learning' - Find ML concepts")
    print("   • 'function' - Find programming functions")
    print("   • 'class' - Find object-oriented programming content")
    print("   • 'fibonacci' - Find specific algorithm content")
    print()
    print("4. 🔄 REFRESH INDEX")
    print("   Tool: refresh_index")
    print("   Parameters:")
    print("   • force: true")
    print("   Expected: Re-indexes all files and shows processing statistics")
    print()
    print("5. 🧪 EXPERIMENT")
    print("   • Add your own files to client_demo/sample_documents/")
    print("   • Use refresh_index to re-scan")
    print("   • Search for content from your new files")
    print()


def validate_environment() -> Tuple[bool, str]:
    """
    Validate that the environment is set up correctly.
    
    Returns:
        Tuple of (success, message) indicating validation result
    """
    if not Path("main.py").exists():
        return False, "main.py not found - run from project root directory"
    
    if not check_dependencies():
        return False, "MCP SDK not available - install with: pip install mcp"
    
    return True, "Environment validation successful"


def main() -> int:
    """
    Main function to run the MCP Inspector demo.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    print_instructions()
    
    config_set = False
    try:
        # Validate environment
        success, message = validate_environment()
        if not success:
            print(f"❌ Environment validation failed: {message}")
            return 1
        
        # Set up demo configuration
        config_set = setup_demo_config()
        if not config_set:
            print("❌ Failed to set up demo configuration")
            return 1
        
        print_demo_examples()
        
        # Ask user if they want to proceed
        response = input("\nWould you like to launch the MCP Inspector now? (y/n): ")
        if response.lower() in ['y', 'yes']:
            success = launch_mcp_inspector()
            if not success:
                return 1
        else:
            print("\nYou can manually launch the MCP Inspector with:")
            print("  python -m mcp dev main.py")
            print("\nOr using uv:")
            print("  uv run mcp dev main.py")
        
        print("\n✅ Demo completed successfully!")
        logger.info("MCP Inspector demo completed successfully")
        return 0
        
    except KeyboardInterrupt:
        print("\n✅ Demo interrupted by user")
        logger.info("Demo interrupted by user")
        return 0
    except (ConfigError, InspectorError) as e:
        print(f"\n❌ Demo failed: {e}")
        logger.error(f"Demo failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        logger.error(f"Unexpected error: {e}")
        return 1
    finally:
        # Clean up configuration
        if config_set:
            try:
                restore_config()
            except ConfigError as e:
                print(f"⚠️  Failed to restore configuration: {e}")
                logger.warning(f"Failed to restore configuration: {e}")


if __name__ == "__main__":
    sys.exit(main())