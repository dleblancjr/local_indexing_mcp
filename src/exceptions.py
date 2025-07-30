"""Custom exceptions for the indexing server."""


class IndexingError(Exception):
    """Base exception for indexing operations."""

    pass


class FileAccessError(IndexingError):
    """Raised when file cannot be read or accessed."""

    pass


class IndexCorruptionError(IndexingError):
    """Raised when index database is corrupted."""

    pass


class ConfigurationError(IndexingError):
    """Raised when configuration is invalid."""

    pass
