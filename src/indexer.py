"""Core indexing logic for processing text files."""
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

from .database import Database
from .exceptions import FileAccessError, IndexingError
from .file_utils import (
    detect_encoding,
    get_file_stats,
    is_text_file,
    is_within_size_limit,
    read_text_file,
)
from .models import FileMetadata, RefreshResult, ServerConfig

logger = logging.getLogger(__name__)


class FileIndexer:
    """Handles file indexing operations."""

    def __init__(self, config: ServerConfig, database: Database):
        """
        Initialize the indexer.

        Args:
            config: Server configuration
            database: Database instance
        """
        self.config = config
        self.db = database
        self.source_path = Path(config['source_directory'])
        self.index_path = Path(config['index_output_directory'])

        # Ensure index directory exists
        self.index_path.mkdir(parents=True, exist_ok=True)

    def _validate_file_path(self, filepath: str) -> Path:
        """
        Validate and resolve file path within source directory.
        
        Args:
            filepath: File path to validate
            
        Returns:
            Validated and resolved Path object
            
        Raises:
            ValueError: If path is outside source directory
        """
        path = Path(filepath)
        
        # Make absolute if relative
        if not path.is_absolute():
            path = self.source_path / path
        
        # Resolve and check if within source directory
        resolved_path = path.resolve()
        source_resolved = self.source_path.resolve()
        
        if not str(resolved_path).startswith(str(source_resolved)):
            raise ValueError(f"Path outside source directory: {filepath}")
        
        return resolved_path

    def scan_directory(self) -> List[Path]:
        """
        Scan source directory for files to index.

        Returns:
            List of file paths that match inclusion criteria
        """
        files = []
        excluded_paths = {self.index_path.resolve()}

        for root, dirs, filenames in os.walk(self.source_path):
            root_path = Path(root)

            # Skip excluded directories
            if root_path.resolve() in excluded_paths:
                dirs.clear()  # Don't descend into this directory
                continue

            for filename in filenames:
                filepath = root_path / filename

                # Check extension filters
                ext = filepath.suffix.lower()

                if self.config['included_extensions']:
                    if ext not in self.config['included_extensions']:
                        continue

                if ext in self.config['excluded_extensions']:
                    continue

                # Check file size
                if not is_within_size_limit(filepath, self.config['max_file_size_mb']):
                    logger.warning(f"Skipping large file: {filepath}")
                    continue

                files.append(filepath)

        return files

    def get_changed_files(self, files: List[Path]) -> List[Path]:
        """
        Filter files that have changed since last index.

        Args:
            files: List of all files

        Returns:
            List of files that need re-indexing
        """
        changed_files = []

        with self.db.get_connection() as conn:
            for filepath in files:
                try:
                    size, mtime = get_file_stats(filepath)

                    # Check if file exists in metadata
                    row = conn.execute(
                        "SELECT size, mtime FROM file_metadata WHERE path = ?",
                        (str(filepath),)
                    ).fetchone()

                    if row is None:
                        # New file
                        changed_files.append(filepath)
                    elif row['size'] != size or row['mtime'] != mtime:
                        # Changed file
                        changed_files.append(filepath)

                except OSError as e:
                    logger.warning(f"Cannot stat file {filepath}: {e}")

        return changed_files

    def index_file(self, filepath: Path) -> bool:
        """
        Index a single file.

        Args:
            filepath: Path to the file

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if it's a text file
            if not is_text_file(filepath):
                logger.debug(f"Skipping binary file: {filepath}")
                return False

            # Get file stats
            size, mtime = get_file_stats(filepath)

            # Detect encoding
            encoding, error = detect_encoding(filepath)
            if encoding is None:
                logger.warning(f"Cannot detect encoding for {filepath}: {error}")
                self._save_file_error(filepath, size, mtime, error)
                return False

            # Read file content
            content, error = read_text_file(filepath, encoding)
            if content is None:
                logger.warning(f"Cannot read {filepath}: {error}")
                self._save_file_error(filepath, size, mtime, error)
                return False

            # Save to database
            with self.db.get_connection() as conn:
                # Remove old entry if exists
                conn.execute("DELETE FROM documents WHERE path = ?", (str(filepath),))
                conn.execute("DELETE FROM file_metadata WHERE path = ?", (str(filepath),))

                # Insert into FTS table
                conn.execute(
                    "INSERT INTO documents (path, content, last_modified) VALUES (?, ?, ?)",
                    (str(filepath), content, datetime.fromtimestamp(mtime).isoformat())
                )

                # Insert metadata
                conn.execute(
                    """INSERT INTO file_metadata 
                       (path, size, mtime, last_indexed, encoding, error) 
                       VALUES (?, ?, ?, ?, ?, NULL)""",
                    (str(filepath), size, mtime, time.time(), encoding)
                )

                conn.commit()

            logger.info(f"Indexed: {filepath}")
            return True

        except Exception as e:
            logger.error(f"Error indexing {filepath}: {e}")
            return False

    def _save_file_error(self, filepath: Path, size: int, mtime: float, error: str) -> None:
        """Save file metadata with error information."""
        try:
            with self.db.get_connection() as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO file_metadata 
                       (path, size, mtime, last_indexed, encoding, error) 
                       VALUES (?, ?, ?, ?, NULL, ?)""",
                    (str(filepath), size, mtime, time.time(), error)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to save error metadata: {e}")

    def remove_deleted_files(self, current_files: Set[Path]) -> int:
        """
        Remove entries for files that no longer exist.

        Args:
            current_files: Set of currently existing files

        Returns:
            Number of files removed
        """
        removed_count = 0
        current_paths = {str(f) for f in current_files}

        with self.db.get_connection() as conn:
            # Get all indexed files
            rows = conn.execute("SELECT path FROM file_metadata").fetchall()

            for row in rows:
                if row['path'] not in current_paths:
                    # File no longer exists
                    conn.execute("DELETE FROM documents WHERE path = ?", (row['path'],))
                    conn.execute("DELETE FROM file_metadata WHERE path = ?", (row['path'],))
                    removed_count += 1
                    logger.info(f"Removed deleted file from index: {row['path']}")

            if removed_count > 0:
                conn.commit()

        return removed_count

    def refresh_index(self, specific_file: Optional[str] = None, force: bool = False) -> RefreshResult:
        """
        Refresh the index, optionally for a specific file.

        Args:
            specific_file: Path to specific file to refresh (None for all)
            force: If True, re-index all files regardless of change detection

        Returns:
            Enhanced result with detailed statistics and timing
        """
        start_time = time.time()
        errors = []
        files_processed = 0
        files_added = 0
        files_updated = 0
        files_removed = 0

        try:
            if specific_file:
                # Index single file with validation
                try:
                    filepath = self._validate_file_path(specific_file)
                except ValueError as e:
                    errors.append(str(e))
                    return self._create_result(start_time, False, 0, 0, 0, 0, errors)

                if filepath.exists():
                    # Check if file already exists in index
                    with self.db.get_connection() as conn:
                        existing = conn.execute(
                            "SELECT path FROM file_metadata WHERE path = ?",
                            (str(filepath),)
                        ).fetchone()
                    
                    if self.index_file(filepath):
                        files_processed = 1
                        if existing:
                            files_updated = 1
                        else:
                            files_added = 1
                    else:
                        errors.append(f"Failed to index {filepath}")
                else:
                    errors.append(f"File not found: {filepath}")
            else:
                # Full directory scan
                logger.info("Starting full directory scan...")
                all_files = self.scan_directory()
                
                # Get files to process based on force flag
                if force:
                    files_to_process = all_files
                    logger.info(f"Force refresh: processing all {len(files_to_process)} files")
                else:
                    files_to_process = self.get_changed_files(all_files)
                    logger.info(f"Found {len(files_to_process)} changed files to index")

                # Track existing files for add/update distinction
                with self.db.get_connection() as conn:
                    existing_files = set(
                        row['path'] for row in 
                        conn.execute("SELECT path FROM file_metadata").fetchall()
                    )

                for filepath in files_to_process:
                    if self.index_file(filepath):
                        files_processed += 1
                        if str(filepath) in existing_files:
                            files_updated += 1
                        else:
                            files_added += 1
                    else:
                        errors.append(f"Failed to index {filepath}")

                # Remove deleted files
                files_removed = self.remove_deleted_files(set(all_files))
                if files_removed > 0:
                    logger.info(f"Removed {files_removed} deleted files from index")

            return self._create_result(
                start_time, len(errors) == 0, files_processed, 
                files_added, files_updated, files_removed, errors
            )

        except Exception as e:
            logger.error(f"Refresh failed: {e}")
            errors.append(str(e))
            return self._create_result(
                start_time, False, files_processed, 
                files_added, files_updated, files_removed, errors
            )

    def _create_result(
        self, 
        start_time: float, 
        success: bool, 
        files_processed: int,
        files_added: int, 
        files_updated: int, 
        files_removed: int, 
        errors: List[str]
    ) -> RefreshResult:
        """
        Create a RefreshResult with timing information.
        
        Args:
            start_time: Start time of the operation
            success: Whether operation was successful
            files_processed: Number of files processed
            files_added: Number of new files added
            files_updated: Number of existing files updated
            files_removed: Number of files removed
            errors: List of error messages
            
        Returns:
            Complete RefreshResult
        """
        return RefreshResult(
            success=success,
            files_processed=files_processed,
            files_added=files_added,
            files_updated=files_updated,
            files_removed=files_removed,
            duration_seconds=round(time.time() - start_time, 2),
            errors=errors
        )
