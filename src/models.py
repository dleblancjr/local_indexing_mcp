"""Type definitions and data models."""
from typing import List, TypedDict


class ServerConfig(TypedDict):
    """Configuration for the MCP indexing server."""

    source_directory: str
    index_output_directory: str
    included_extensions: List[str]
    excluded_extensions: List[str]
    scan_interval_seconds: int
    max_file_size_mb: float


class SearchResult(TypedDict):
    """Result from a search query."""

    path: str
    snippet: str
    score: float
    last_modified: str


class IndexStats(TypedDict):
    """Statistics about the current index."""

    indexed_files: int
    last_scan: str
    index_size_mb: float
    total_documents: int
    errors_encountered: int


class RefreshResult(TypedDict):
    """Result from a refresh operation."""

    success: bool
    files_processed: int
    files_added: int
    files_updated: int
    files_removed: int
    duration_seconds: float
    errors: List[str]


class FileMetadata(TypedDict):
    """Metadata for a tracked file."""

    size: int
    mtime: float
    last_indexed: float
    encoding: str
    error: str
