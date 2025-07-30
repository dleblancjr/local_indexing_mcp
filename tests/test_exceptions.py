"""Tests for custom exceptions."""
import pytest

from src.exceptions import (
    ConfigurationError,
    FileAccessError,
    IndexCorruptionError,
    IndexingError,
)


class TestExceptions:
    """Test custom exception classes."""

    def test_indexing_error_base(self):
        """Test base IndexingError exception."""
        with pytest.raises(IndexingError) as exc_info:
            raise IndexingError("Base indexing error")

        assert str(exc_info.value) == "Base indexing error"
        assert isinstance(exc_info.value, Exception)

    def test_file_access_error(self):
        """Test FileAccessError exception."""
        with pytest.raises(FileAccessError) as exc_info:
            raise FileAccessError("Cannot read file: /path/to/file.txt")

        assert "Cannot read file" in str(exc_info.value)
        assert isinstance(exc_info.value, IndexingError)
        assert isinstance(exc_info.value, Exception)

    def test_index_corruption_error(self):
        """Test IndexCorruptionError exception."""
        with pytest.raises(IndexCorruptionError) as exc_info:
            raise IndexCorruptionError("Database integrity check failed")

        assert "Database integrity" in str(exc_info.value)
        assert isinstance(exc_info.value, IndexingError)

    def test_configuration_error(self):
        """Test ConfigurationError exception."""
        with pytest.raises(ConfigurationError) as exc_info:
            raise ConfigurationError("Missing required field: source_directory")

        assert "Missing required field" in str(exc_info.value)
        assert isinstance(exc_info.value, IndexingError)

    def test_exception_inheritance(self):
        """Test that all custom exceptions inherit from IndexingError."""
        # Create instances
        base_error = IndexingError("base")
        file_error = FileAccessError("file")
        corruption_error = IndexCorruptionError("corruption")
        config_error = ConfigurationError("config")

        # Test inheritance
        assert isinstance(file_error, IndexingError)
        assert isinstance(corruption_error, IndexingError)
        assert isinstance(config_error, IndexingError)

        # Test that they can be caught by base class
        errors = [file_error, corruption_error, config_error]

        for error in errors:
            try:
                raise error
            except IndexingError:
                pass  # Should be caught
            except Exception:
                assert False  # Should not reach here

    def test_exception_with_no_message(self):
        """Test exceptions can be raised without message."""
        with pytest.raises(IndexingError) as exc_info:
            raise IndexingError()

        assert str(exc_info.value) == ""

    def test_exception_with_formatted_message(self):
        """Test exceptions with formatted messages."""
        path = "/test/file.txt"
        size = 1024

        with pytest.raises(FileAccessError) as exc_info:
            raise FileAccessError(f"File {path} exceeds size limit: {size} bytes")

        assert path in str(exc_info.value)
        assert str(size) in str(exc_info.value)

    def test_exception_chaining(self):
        """Test exception chaining with 'from' clause."""
        original_error = ValueError("Original error")

        with pytest.raises(ConfigurationError) as exc_info:
            try:
                raise original_error
            except ValueError as e:
                raise ConfigurationError("Configuration failed") from e

        assert str(exc_info.value) == "Configuration failed"
        assert exc_info.value.__cause__ is original_error

    def test_catching_specific_exceptions(self):
        """Test catching specific exception types."""
        def raise_file_error():
            raise FileAccessError("File error")

        def raise_config_error():
            raise ConfigurationError("Config error")

        # Should catch only FileAccessError
        try:
            raise_file_error()
        except FileAccessError:
            pass  # Expected
        except ConfigurationError:
            assert False  # Should not catch this

        # Should catch only ConfigurationError
        try:
            raise_config_error()
        except FileAccessError:
            assert False  # Should not catch this
        except ConfigurationError:
            pass  # Expected
