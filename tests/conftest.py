"""Pytest configuration and fixtures."""
import json
import tempfile
from pathlib import Path
from typing import Dict, Generator

import pytest

from src.database import Database
from src.models import ServerConfig


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_config(temp_dir: Path) -> ServerConfig:
    """Create a sample configuration for testing."""
    source_dir = temp_dir / "source"
    source_dir.mkdir()

    index_dir = temp_dir / "indexes"
    index_dir.mkdir()

    return ServerConfig(
        source_directory=str(source_dir),
        index_output_directory=str(index_dir),
        included_extensions=[".txt", ".md"],
        excluded_extensions=[],
        scan_interval_seconds=300,
        max_file_size_mb=10
    )


@pytest.fixture
def config_file(temp_dir: Path, sample_config: ServerConfig) -> Path:
    """Create a configuration file for testing."""
    config_path = temp_dir / "config.json"
    with open(config_path, 'w') as f:
        json.dump(sample_config, f)
    return config_path


@pytest.fixture
def test_database(temp_dir: Path) -> Database:
    """Create a test database instance."""
    db_path = temp_dir / "test.db"
    return Database(db_path)


@pytest.fixture
def sample_text_files(temp_dir: Path) -> Dict[str, Path]:
    """Create sample text files for testing."""
    source_dir = temp_dir / "source"
    source_dir.mkdir(exist_ok=True)

    files = {}

    # Create various text files
    files['simple'] = source_dir / "simple.txt"
    files['simple'].write_text("This is a simple text file for testing.")

    files['markdown'] = source_dir / "document.md"
    files['markdown'].write_text("""# Test Document

This is a **markdown** document with some content.

## Section 1
Testing the search functionality.

## Section 2
More content for indexing.""")

    files['nested'] = source_dir / "subdir" / "nested.txt"
    files['nested'].parent.mkdir()
    files['nested'].write_text("This file is in a subdirectory.")

    # Create a non-text file (should be skipped)
    files['binary'] = source_dir / "binary.bin"
    files['binary'].write_bytes(b'\x00\x01\x02\x03\x04')

    # Create a large file (for size limit testing)
    files['large'] = source_dir / "large.txt"
    files['large'].write_text("Large content. " * 100000)  # ~1.4 MB

    return files


@pytest.fixture
def mock_mcp_server():
    """Create a mock MCP server for testing."""
    from unittest.mock import Mock, AsyncMock

    server = Mock()
    server.list_tools = AsyncMock()
    server.call_tool = AsyncMock()

    return server
