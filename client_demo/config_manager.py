#!/usr/bin/env python3
"""
Configuration management utilities for demo scripts.

This module provides common configuration management functionality
used across all demo scripts.
"""

import logging
import shutil
from pathlib import Path
from typing import Tuple

logger = logging.getLogger(__name__)

# Constants
DEMO_CONFIG_PATH = Path("client_demo/demo_config.json")
MAIN_CONFIG_PATH = Path("config.json")
BACKUP_CONFIG_PATH = Path("config.json.backup")


class ConfigError(Exception):
    """Custom exception for configuration-related errors."""
    pass


def setup_demo_config() -> bool:
    """
    Set up the demo configuration for testing.
    
    Backs up existing config and copies demo config to main location.
    
    Returns:
        True if setup was successful, False if demo config doesn't exist
        
    Raises:
        ConfigError: If file operations fail
    """
    try:
        if not DEMO_CONFIG_PATH.exists():
            logger.warning(f"Demo config not found at {DEMO_CONFIG_PATH}")
            return False
        
        # Backup existing config if any
        if MAIN_CONFIG_PATH.exists():
            shutil.copy(MAIN_CONFIG_PATH, BACKUP_CONFIG_PATH)
            logger.info("Backed up existing configuration")
        
        # Copy demo config
        shutil.copy(DEMO_CONFIG_PATH, MAIN_CONFIG_PATH)
        logger.info("Demo configuration set up successfully")
        return True
        
    except (OSError, IOError) as e:
        logger.error(f"Failed to set up demo config: {e}")
        raise ConfigError(f"Configuration setup failed: {e}") from e


def restore_config() -> None:
    """
    Restore the original configuration.
    
    Restores backed up config or removes demo config if no backup exists.
    
    Raises:
        ConfigError: If file operations fail
    """
    try:
        if BACKUP_CONFIG_PATH.exists():
            shutil.copy(BACKUP_CONFIG_PATH, MAIN_CONFIG_PATH)
            BACKUP_CONFIG_PATH.unlink()
            logger.info("Original configuration restored")
        elif MAIN_CONFIG_PATH.exists():
            MAIN_CONFIG_PATH.unlink()
            logger.info("Demo configuration cleaned up")
        else:
            logger.info("No configuration to restore")
            
    except (OSError, IOError) as e:
        logger.error(f"Failed to restore config: {e}")
        raise ConfigError(f"Configuration restore failed: {e}") from e


def validate_demo_paths() -> Tuple[bool, str]:
    """
    Validate that demo paths and files exist.
    
    Returns:
        Tuple of (success, message) indicating validation result
    """
    if not DEMO_CONFIG_PATH.exists():
        return False, f"Demo config file not found: {DEMO_CONFIG_PATH}"
    
    sample_docs = Path("client_demo/sample_documents")
    if not sample_docs.exists():
        return False, f"Sample documents directory not found: {sample_docs}"
    
    if not any(sample_docs.iterdir()):
        return False, "Sample documents directory is empty"
    
    main_py = Path("main.py")
    if not main_py.exists():
        return False, "main.py not found (run from project root)"
    
    return True, "All demo paths validated successfully"