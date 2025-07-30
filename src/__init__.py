"""Local indexing MCP server package."""

__version__ = "0.1.0"
__author__ = "Local Indexing MCP Team"

# Public API
from .config import load_config, validate_config
from .database import Database
from .exceptions import (
    ConfigurationError,
    FileAccessError,
    IndexCorruptionError,
    IndexingError,
)
from .file_utils import (
    detect_encoding,
    get_file_stats,
    is_text_file,
    read_text_file,
)
from .indexer import FileIndexer
from .models import (
    FileMetadata,
    IndexStats,
    RefreshResult,
    SearchResult,
    ServerConfig,
)
from .search import SearchEngine

__all__ = [
    # Version
    "__version__",
    # Configuration
    "load_config",
    "validate_config",
    # Database
    "Database",
    # Exceptions
    "ConfigurationError",
    "FileAccessError",
    "IndexCorruptionError",
    "IndexingError",
    # File utilities
    "detect_encoding",
    "get_file_stats",
    "is_text_file",
    "read_text_file",
    # Core classes
    "FileIndexer",
    "SearchEngine",
    # Models
    "FileMetadata",
    "IndexStats",
    "RefreshResult",
    "SearchResult",
    "ServerConfig",
]
