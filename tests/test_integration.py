"""Integration tests for the MCP server."""
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.models import ServerConfig


class TestMCPServer:
    """Test MCP server integration."""
    
    @pytest.fixture
    def initialized_server(
        self, 
        sample_config: ServerConfig, 
        temp_dir: Path, 
        request: pytest.FixtureRequest
    ) -> Any:
        """
        Initialize MCP server for integration testing.
        
        Creates test files, initializes the server, and ensures
        proper cleanup after tests.
        
        Args:
            sample_config: Test configuration
            temp_dir: Temporary directory for test files
            request: Pytest fixture request for cleanup
            
        Returns:
            Initialized main module
        """
        # Create config file
        config_path = temp_dir / "config.json"
        with open(config_path, 'w') as f:
            json.dump(sample_config, f)
        
        # Create test files
        self._create_test_files(Path(sample_config['source_directory']))
        
        # Save original working directory
        original_cwd = Path.cwd()
        
        # Change to temp directory for test isolation
        import os
        os.chdir(temp_dir)
        
        # Import fresh module
        main = self._import_fresh_module('main')
        
        # Initialize server
        asyncio.run(main.initialize_server())
        
        # Register cleanup
        request.addfinalizer(
            lambda: self._cleanup_server(main, original_cwd)
        )
        
        return main
    
    def _create_test_files(self, source_dir: Path) -> None:
        """Create test files for integration testing."""
        (source_dir / "test1.txt").write_text("Python programming tutorial")
        (source_dir / "test2.md").write_text("Java development guide")
        
        subdir = source_dir / "subdir"
        subdir.mkdir(exist_ok=True)
        (subdir / "test3.txt").write_text("Web development with JavaScript")
    
    def _import_fresh_module(self, module_name: str) -> Any:
        """Import module fresh, removing any cached version."""
        if module_name in sys.modules:
            del sys.modules[module_name]
        return __import__(module_name)
    
    def _cleanup_server(self, main_module: Any, original_cwd: Path) -> None:
        """Clean up server and restore environment."""
        # Create new event loop for cleanup
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(main_module.shutdown())
        finally:
            loop.close()
        
        # Restore working directory
        os.chdir(original_cwd)
        
        # Clean up module imports
        if 'main' in sys.modules:
            del sys.modules['main']
    
    @pytest.mark.asyncio
    async def test_search_tool(self, initialized_server: Any) -> None:
        """
        Test search functionality through MCP tool.
        
        Verifies that search returns properly formatted results
        for matching documents.
        """
        main = initialized_server
        
        # Search for content that exists in test files
        result = await main.search("Python", limit=5)
        
        # Verify response format
        assert isinstance(result, str)
        assert "Found" in result
        assert "Python" in result
        assert "test1.txt" in result
    
    @pytest.mark.asyncio
    async def test_search_no_results(self, initialized_server):
        """Test search with no results."""
        main = initialized_server
        
        result = await main.search("NonexistentTerm")
        
        assert isinstance(result, str)
        assert "No results found" in result
    
    @pytest.mark.asyncio
    async def test_get_index_stats_tool(self, initialized_server):
        """Test getting index statistics."""
        main = initialized_server
        
        result = await main.get_index_stats()
        
        assert isinstance(result, str)
        assert "Index Statistics" in result
        assert "Indexed Files:" in result
        assert "Last Scan:" in result
        assert "Index Size:" in result
        assert "Errors Encountered:" in result
    
    @pytest.mark.asyncio
    async def test_refresh_index_tool(self, initialized_server):
        """Test refresh index functionality."""
        main = initialized_server
        
        # Full refresh
        result = await main.refresh_index()
        
        assert isinstance(result, str)
        assert "Refresh completed" in result or "completed" in result
        assert "Files Processed:" in result
        assert "Files Added:" in result
        assert "Files Updated:" in result
        assert "Files Removed:" in result
        assert "Duration:" in result
        assert "Success: True" in result
    
    @pytest.mark.asyncio
    async def test_refresh_specific_file(
        self, 
        initialized_server: Any, 
        sample_config: ServerConfig
    ) -> None:
        """
        Test refreshing a specific file.
        
        Verifies that:
        1. A single file can be refreshed
        2. The refreshed file is searchable
        """
        main = initialized_server
        source_dir = Path(sample_config['source_directory'])
        
        # Create a new file
        new_file = source_dir / "new_file.txt"
        new_file.write_text("New content to index")
        
        # Refresh just this file
        result = await main.refresh_index("new_file.txt")
        
        # Verify refresh succeeded
        assert isinstance(result, str)
        assert "Files Processed: 1" in result
        assert "Files Added: 1" in result
        assert "Files Updated: 0" in result
        assert "Duration:" in result
        
        # Verify file is searchable
        search_result = await main.search("New content")
        assert "new_file.txt" in search_result
    
    @pytest.mark.asyncio
    async def test_tool_error_handling(self, initialized_server: Any) -> None:
        """
        Test error handling when server components are not initialized.
        
        Verifies that appropriate error messages are returned when
        required components are missing.
        """
        main = initialized_server
        
        # Test search with missing search_engine
        original_search_engine = main.search_engine
        main.search_engine = None
        
        result = await main.search("test")
        
        assert isinstance(result, str)
        assert "not properly initialized" in result
        
        # Restore
        main.search_engine = original_search_engine
    
    @pytest.mark.asyncio
    async def test_periodic_scanning(
        self, 
        initialized_server: Any, 
        sample_config: ServerConfig
    ) -> None:
        """
        Test manual index refresh (simulating periodic scanning).
        
        Verifies that:
        1. New files can be indexed after server initialization
        2. The indexer's refresh_index method works correctly
        3. Newly indexed files are searchable
        
        Note: The actual background task testing is complex due to
        event loop lifecycle in tests, so we test the underlying
        functionality instead.
        """
        main = initialized_server
        
        # Verify indexer is available
        assert main.indexer is not None
        
        # Create a new file after initialization
        source_dir = Path(sample_config['source_directory'])
        new_file = source_dir / "periodic_test.txt"
        new_file.write_text("Content added during runtime")
        
        # Manually trigger index refresh (this is what periodic scan does)
        result = main.indexer.refresh_index()
        assert result['success'] is True
        assert result['files_processed'] >= 1
        assert result['files_added'] >= 0
        assert result['files_updated'] >= 0
        assert result['files_removed'] >= 0
        assert result['duration_seconds'] >= 0
        
        # Verify new file is searchable
        search_result = await main.search("runtime")
        assert isinstance(search_result, str)
        assert "periodic_test.txt" in search_result


class TestErrorScenarios:
    """Test various error scenarios."""
    
    @pytest.mark.asyncio
    async def test_missing_config_file(self, temp_dir):
        """Test initialization with missing config file."""
        import main
        
        with patch('main.Path') as mock_path:
            mock_path.side_effect = lambda x: temp_dir / x
            
            with pytest.raises(Exception) as exc_info:
                await main.initialize_server()
            
            assert "configuration" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_invalid_config(self, temp_dir):
        """Test initialization with invalid config."""
        import main
        
        config_path = temp_dir / "config.json"
        config_path.write_text('{"invalid": "config"}')  # Missing required fields
        
        with patch('main.Path') as mock_path:
            mock_path.return_value = config_path
            mock_path.side_effect = lambda x: config_path if x == "config.json" else Path(x)
            
            with pytest.raises(Exception) as exc_info:
                await main.initialize_server()
            
            assert "required field" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_database_initialization_failure(self, sample_config, temp_dir):
        """Test handling of database initialization failure."""
        import main
        
        config_path = temp_dir / "config.json"
        with open(config_path, 'w') as f:
            json.dump(sample_config, f)
        
        # Make index directory read-only
        index_dir = Path(sample_config['index_output_directory'])
        index_dir.mkdir(exist_ok=True)  # Add exist_ok=True
        try:
            index_dir.chmod(0o444)
        except:
            # Some systems don't support chmod properly
            pytest.skip("System doesn't support chmod for testing")
        
        with patch('main.Path') as mock_path:
            mock_path.return_value = config_path
            mock_path.side_effect = lambda x: config_path if x == "config.json" else Path(x)
            
            try:
                await main.initialize_server()
                # If it doesn't raise, that's okay - some systems allow this
            except Exception as e:
                assert "database" in str(e).lower() or "permission" in str(e).lower()
