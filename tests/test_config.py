"""Tests for configuration loading and validation."""
import json
from pathlib import Path

import pytest

from src.config import load_config, validate_config
from src.exceptions import ConfigurationError


class TestConfigLoading:
    """Test configuration loading functionality."""

    def test_load_valid_config(self, config_file):
        """Test loading a valid configuration file."""
        config = load_config(config_file)

        assert 'source_directory' in config
        assert 'index_output_directory' in config
        assert config['scan_interval_seconds'] == 300
        assert config['max_file_size_mb'] == 10

    def test_load_missing_config(self, temp_dir):
        """Test loading a non-existent configuration file."""
        missing_path = temp_dir / "missing.json"

        with pytest.raises(ConfigurationError) as exc_info:
            load_config(missing_path)

        assert "not found" in str(exc_info.value)

    def test_load_invalid_json(self, temp_dir):
        """Test loading an invalid JSON file."""
        invalid_json = temp_dir / "invalid.json"
        invalid_json.write_text("{invalid json content")

        with pytest.raises(ConfigurationError) as exc_info:
            load_config(invalid_json)

        assert "Invalid JSON" in str(exc_info.value)


class TestConfigValidation:
    """Test configuration validation."""

    def test_validate_minimal_config(self, temp_dir):
        """Test validation with minimal required fields."""
        source_dir = temp_dir / "source"
        source_dir.mkdir()

        minimal_config = {
            'source_directory': str(source_dir)
        }

        config = validate_config(minimal_config)

        # Check defaults were applied
        assert config['index_output_directory'] == './indexes'
        assert config['included_extensions'] == ['.txt', '.md', '.rst']
        assert config['excluded_extensions'] == []
        assert config['scan_interval_seconds'] == 300
        assert config['max_file_size_mb'] == 10

    def test_missing_required_field(self):
        """Test validation with missing required field."""
        config_data = {
            'index_output_directory': './indexes'
        }

        with pytest.raises(ConfigurationError) as exc_info:
            validate_config(config_data)

        assert "Missing required field: source_directory" in str(exc_info.value)

    def test_nonexistent_source_directory(self, temp_dir):
        """Test validation with non-existent source directory."""
        config_data = {
            'source_directory': str(temp_dir / "nonexistent")
        }

        with pytest.raises(ConfigurationError) as exc_info:
            validate_config(config_data)

        assert "does not exist" in str(exc_info.value)

    def test_source_not_directory(self, temp_dir):
        """Test validation when source path is not a directory."""
        file_path = temp_dir / "file.txt"
        file_path.write_text("content")

        config_data = {
            'source_directory': str(file_path)
        }

        with pytest.raises(ConfigurationError) as exc_info:
            validate_config(config_data)

        assert "not a directory" in str(exc_info.value)

    def test_same_source_and_index_directory(self, temp_dir):
        """Test validation when source and index directories are the same."""
        source_dir = temp_dir / "source"
        source_dir.mkdir()

        config_data = {
            'source_directory': str(source_dir),
            'index_output_directory': str(source_dir)
        }

        with pytest.raises(ConfigurationError) as exc_info:
            validate_config(config_data)

        assert "cannot be the same" in str(exc_info.value)

    def test_invalid_scan_interval(self, temp_dir):
        """Test validation with invalid scan interval."""
        source_dir = temp_dir / "source"
        source_dir.mkdir()

        config_data = {
            'source_directory': str(source_dir),
            'scan_interval_seconds': 30  # Too low
        }

        with pytest.raises(ConfigurationError) as exc_info:
            validate_config(config_data)

        assert "at least 60 seconds" in str(exc_info.value)

    def test_invalid_max_file_size(self, temp_dir):
        """Test validation with invalid max file size."""
        source_dir = temp_dir / "source"
        source_dir.mkdir()

        # Test too small
        config_data = {
            'source_directory': str(source_dir),
            'max_file_size_mb': 0
        }

        with pytest.raises(ConfigurationError) as exc_info:
            validate_config(config_data)

        assert "between 0 and 100 MB" in str(exc_info.value)

        # Test too large
        config_data['max_file_size_mb'] = 200

        with pytest.raises(ConfigurationError) as exc_info:
            validate_config(config_data)

        assert "between 0 and 100 MB" in str(exc_info.value)

    def test_invalid_extension_format(self, temp_dir):
        """Test validation with invalid extension format."""
        source_dir = temp_dir / "source"
        source_dir.mkdir()

        config_data = {
            'source_directory': str(source_dir),
            'included_extensions': ['txt', '.md']  # Missing dot
        }

        with pytest.raises(ConfigurationError) as exc_info:
            validate_config(config_data)

        assert "Extensions must start with '.'" in str(exc_info.value)
