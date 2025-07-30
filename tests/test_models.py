"""Tests for data models."""
from datetime import datetime

import pytest

from src.models import (
    FileMetadata,
    IndexStats,
    RefreshResult,
    SearchResult,
    ServerConfig,
)


class TestDataModels:
    """Test TypedDict data models."""

    def test_server_config_creation(self):
        """Test ServerConfig creation with all fields."""
        config = ServerConfig(
            source_directory="/path/to/source",
            index_output_directory="/path/to/index",
            included_extensions=[".txt", ".md"],
            excluded_extensions=[".tmp"],
            scan_interval_seconds=300,
            max_file_size_mb=10.5
        )

        assert config['source_directory'] == "/path/to/source"
        assert config['index_output_directory'] == "/path/to/index"
        assert len(config['included_extensions']) == 2
        assert config['scan_interval_seconds'] == 300
        assert config['max_file_size_mb'] == 10.5

    def test_search_result_creation(self):
        """Test SearchResult creation."""
        result = SearchResult(
            path="/docs/test.txt",
            snippet="This is a <mark>test</mark> snippet...",
            score=0.95,
            last_modified="2024-01-01T10:00:00"
        )

        assert result['path'] == "/docs/test.txt"
        assert "<mark>" in result['snippet']
        assert result['score'] == 0.95
        assert "2024-01-01" in result['last_modified']

    def test_index_stats_creation(self):
        """Test IndexStats creation."""
        stats = IndexStats(
            indexed_files=100,
            last_scan="2024-01-01T12:00:00",
            index_size_mb=5.25,
            total_documents=100,
            errors_encountered=2
        )

        assert stats['indexed_files'] == 100
        assert stats['last_scan'] == "2024-01-01T12:00:00"
        assert stats['index_size_mb'] == 5.25
        assert stats['total_documents'] == 100
        assert stats['errors_encountered'] == 2

    def test_refresh_result_creation(self):
        """Test RefreshResult creation."""
        result = RefreshResult(
            success=True,
            files_processed=50,
            errors=[]
        )

        assert result['success'] is True
        assert result['files_processed'] == 50
        assert len(result['errors']) == 0

        # Test with errors
        result_with_errors = RefreshResult(
            success=False,
            files_processed=48,
            errors=["Failed to read file1.txt", "Encoding error in file2.txt"]
        )

        assert result_with_errors['success'] is False
        assert result_with_errors['files_processed'] == 48
        assert len(result_with_errors['errors']) == 2

    def test_file_metadata_creation(self):
        """Test FileMetadata creation."""
        metadata = FileMetadata(
            size=1024,
            mtime=1704110400.0,  # 2024-01-01 12:00:00 UTC
            last_indexed=1704114000.0,  # 2024-01-01 13:00:00 UTC
            encoding="utf-8",
            error=""
        )

        assert metadata['size'] == 1024
        assert metadata['mtime'] == 1704110400.0
        assert metadata['last_indexed'] == 1704114000.0
        assert metadata['encoding'] == "utf-8"
        assert metadata['error'] == ""

    def test_model_field_access(self):
        """Test that TypedDict fields can be accessed like dict."""
        config = ServerConfig(
            source_directory="/test",
            index_output_directory="./index",
            included_extensions=[],
            excluded_extensions=[],
            scan_interval_seconds=60,
            max_file_size_mb=1
        )

        # Test dict-like access
        assert config['source_directory'] == "/test"
        assert 'index_output_directory' in config
        assert len(config) == 6  # All fields

        # Test iteration
        keys = list(config.keys())
        assert 'source_directory' in keys
        assert 'scan_interval_seconds' in keys

    def test_model_type_validation_at_runtime(self):
        """Test that models accept correct types at runtime."""
        # TypedDict doesn't enforce types at runtime, but we can test
        # that our code uses correct types

        # This should work (correct types)
        try:
            stats = IndexStats(
                indexed_files=100,
                last_scan="2024-01-01T00:00:00",
                index_size_mb=1.5,
                total_documents=100,
                errors_encountered=0
            )
            assert True  # Should succeed
        except TypeError:
            assert False  # Should not raise

        # Note: TypedDict doesn't prevent wrong types at runtime
        # This is just for documentation and type checking
        stats_wrong = IndexStats(
            indexed_files="100",  # Wrong type, but TypedDict allows it
            last_scan="2024-01-01T00:00:00",
            index_size_mb=1.5,
            total_documents=100,
            errors_encountered=0
        )
        # This will work at runtime, but mypy would catch it
        assert stats_wrong['indexed_files'] == "100"
