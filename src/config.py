"""Configuration loading and validation."""
import json
import logging
from pathlib import Path
from typing import Dict, Any

from .exceptions import ConfigurationError
from .models import ServerConfig

logger = logging.getLogger(__name__)


def load_config(config_path: Path) -> ServerConfig:
    """
    Load and validate configuration from JSON file.

    Args:
        config_path: Path to the configuration file

    Returns:
        Validated server configuration

    Raises:
        ConfigurationError: If configuration is invalid or missing required fields
    """
    try:
        with open(config_path, 'r') as f:
            config_data = json.load(f)
    except FileNotFoundError:
        raise ConfigurationError(f"Configuration file not found: {config_path}")
    except json.JSONDecodeError as e:
        raise ConfigurationError(f"Invalid JSON in configuration file: {e}")

    # Validate and set defaults
    config = validate_config(config_data)
    return config


def validate_config(config_data: Dict[str, Any]) -> ServerConfig:
    """
    Validate configuration data and apply defaults.

    Args:
        config_data: Raw configuration dictionary

    Returns:
        Validated configuration with defaults applied

    Raises:
        ConfigurationError: If required fields are missing or invalid
    """
    # Check required fields
    if 'source_directory' not in config_data:
        raise ConfigurationError("Missing required field: source_directory")

    source_dir = Path(config_data['source_directory'])
    if not source_dir.exists():
        raise ConfigurationError(f"Source directory does not exist: {source_dir}")
    if not source_dir.is_dir():
        raise ConfigurationError(f"Source path is not a directory: {source_dir}")

    # Apply defaults
    config: ServerConfig = {
        'source_directory': str(source_dir.resolve()),
        'index_output_directory': config_data.get('index_output_directory', './indexes'),
        'included_extensions': config_data.get('included_extensions', ['.txt', '.md', '.rst']),
        'excluded_extensions': config_data.get('excluded_extensions', []),
        'scan_interval_seconds': config_data.get('scan_interval_seconds', 300),
        'max_file_size_mb': config_data.get('max_file_size_mb', 10),
    }

    # Validate other fields
    index_dir = Path(config['index_output_directory'])

    # Ensure source and index directories are different
    if source_dir.resolve() == index_dir.resolve():
        raise ConfigurationError("Source and index directories cannot be the same")

    # Validate scan interval
    if config['scan_interval_seconds'] < 60:
        raise ConfigurationError("Scan interval must be at least 60 seconds")

    # Validate max file size
    if config['max_file_size_mb'] <= 0 or config['max_file_size_mb'] > 100:
        raise ConfigurationError("Max file size must be between 0 and 100 MB")

    # Validate extensions
    for ext in config['included_extensions'] + config['excluded_extensions']:
        if not ext.startswith('.'):
            raise ConfigurationError(f"Extensions must start with '.': {ext}")

    logger.info(f"Configuration loaded successfully from {source_dir}")
    return config
