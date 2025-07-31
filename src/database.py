"""SQLite database operations and schema management."""
import logging
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional

from .exceptions import IndexCorruptionError

logger = logging.getLogger(__name__)

# Constants for database validation and operations
MIN_SQLITE_FILE_SIZE = 100  # Minimum bytes for a valid SQLite file
SQLITE_HEADER_SIGNATURE = b'SQLite format 3\x00'  # Standard SQLite file header
DB_CREATION_DELAY = 0.1  # Delay in seconds after file deletion


SCHEMA_SQL = """
-- Enable FTS5 if not already enabled
PRAGMA compile_options;

-- Create FTS5 virtual table for searchable content
CREATE VIRTUAL TABLE IF NOT EXISTS documents USING fts5(
    path UNINDEXED,
    content,
    last_modified UNINDEXED,
    tokenize='porter'
);

-- Metadata table for change tracking
CREATE TABLE IF NOT EXISTS file_metadata (
    path TEXT PRIMARY KEY,
    size INTEGER NOT NULL,
    mtime REAL NOT NULL,
    last_indexed REAL NOT NULL,
    encoding TEXT,
    error TEXT
);

-- Index for efficient change detection
CREATE INDEX IF NOT EXISTS idx_mtime ON file_metadata(mtime);
"""


class Database:
    """Manages SQLite database connections and operations."""

    def __init__(self, db_path: Path):
        """
        Initialize database manager.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        """
        Create database schema if it doesn't exist.
        
        Handles corrupted databases by removing and recreating them.
        
        Raises:
            IndexCorruptionError: If database cannot be initialized
        """
        if self.db_path.exists():
            if not self._validate_existing_database():
                logger.warning(
                    f"Removing corrupted database at {self.db_path}"
                )
                self._remove_database_files()
        
        self._create_schema()
    
    def _remove_database_files(self) -> None:
        """
        Remove database file and all associated journal files.
        
        SQLite in WAL mode creates additional files (.db-wal, .db-shm)
        that must be removed when cleaning up a corrupted database.
        """
        # Remove main database file
        if self.db_path.exists():
            self.db_path.unlink()
            logger.debug(
                f"Removed database file",
                extra={"db_path": str(self.db_path)}
            )
        
        # Remove WAL file
        wal_path = Path(str(self.db_path) + "-wal")
        if wal_path.exists():
            wal_path.unlink()
            logger.debug(
                f"Removed WAL file",
                extra={"wal_path": str(wal_path)}
            )
        
        # Remove shared memory file
        shm_path = Path(str(self.db_path) + "-shm")
        if shm_path.exists():
            shm_path.unlink()
            logger.debug(
                f"Removed shared memory file",
                extra={"shm_path": str(shm_path)}
            )
    
    def _validate_existing_database(self) -> bool:
        """
        Validate that existing database file is accessible.
        
        Returns:
            True if database is valid, False if corrupted
        """
        # First, check if it's a reasonable size for a SQLite database
        try:
            file_size = self.db_path.stat().st_size
            if file_size < MIN_SQLITE_FILE_SIZE:  # SQLite databases have headers
                logger.debug(
                    f"Database file too small to be valid",
                    extra={"db_path": str(self.db_path), "size": file_size}
                )
                return False
        except Exception as e:
            logger.error(
                f"Cannot stat database file: {e}",
                extra={"db_path": str(self.db_path)}
            )
            return False
        
        # Try to read the SQLite header
        try:
            with open(self.db_path, 'rb') as f:
                header = f.read(16)
                if header != SQLITE_HEADER_SIGNATURE:
                    logger.debug(
                        f"Invalid SQLite header",
                        extra={"db_path": str(self.db_path)}
                    )
                    return False
        except Exception as e:
            logger.error(
                f"Cannot read database header: {e}",
                extra={"db_path": str(self.db_path)}
            )
            return False
        
        # Now try actual connection
        test_conn: Optional[sqlite3.Connection] = None
        try:
            test_conn = sqlite3.connect(str(self.db_path))
            test_conn.execute("SELECT 1")
            return True
        except sqlite3.DatabaseError as e:
            logger.error(
                f"Database validation failed - DatabaseError: {e}",
                extra={"db_path": str(self.db_path)}
            )
            return False
        except sqlite3.OperationalError as e:
            logger.error(
                f"Database validation failed - OperationalError: {e}",
                extra={"db_path": str(self.db_path)}
            )
            return False
        except Exception as e:
            logger.error(
                f"Database validation failed - unexpected error: {e}",
                extra={"db_path": str(self.db_path), "error_type": type(e).__name__}
            )
            return False
        finally:
            if test_conn:
                test_conn.close()
    
    def _create_schema(self) -> None:
        """
        Create database schema.
        
        Creates the database file if it doesn't exist and sets up
        the required tables and indexes.
        
        Raises:
            IndexCorruptionError: If schema creation fails
        """
        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Ensure we start with a clean slate
        if self.db_path.exists():
            logger.warning(
                f"Database file still exists before creation, removing it",
                extra={"db_path": str(self.db_path)}
            )
            self._remove_database_files()
            
            # Small delay to ensure file system has completed deletion
            time.sleep(DB_CREATION_DELAY)
        
        conn: Optional[sqlite3.Connection] = None
        try:
            # Create fresh connection (this creates the file)
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            
            # Set pragmas for performance
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            
            # Create schema
            conn.executescript(SCHEMA_SQL)
            conn.commit()
            
            logger.info(
                f"Database schema initialized successfully",
                extra={"db_path": str(self.db_path)}
            )
        except sqlite3.Error as e:
            logger.error(
                f"Failed to create database schema: {e}",
                extra={
                    "db_path": str(self.db_path),
                    "error_type": type(e).__name__,
                    "error_msg": str(e)
                }
            )
            raise IndexCorruptionError(f"Failed to initialize database: {e}") from e
        finally:
            if conn:
                conn.close()

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Get a database connection context manager.

        Yields:
            SQLite connection object with Row factory enabled

        Raises:
            IndexCorruptionError: If database cannot be accessed
        """
        conn: Optional[sqlite3.Connection] = None
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            yield conn
        except sqlite3.OperationalError as e:
            error_msg = str(e).lower()
            if "file is not a database" in error_msg:
                logger.error(
                    f"Database file is corrupted: {e}",
                    extra={"db_path": str(self.db_path)}
                )
                raise IndexCorruptionError(f"Database error: {e}") from e
            elif "database disk image is malformed" in error_msg:
                logger.error(
                    f"Database disk image is malformed: {e}",
                    extra={"db_path": str(self.db_path)}
                )
                raise IndexCorruptionError(f"Database error: {e}") from e
            else:
                logger.error(
                    f"Database operational error: {e}",
                    extra={"db_path": str(self.db_path)}
                )
                raise IndexCorruptionError(f"Database operation error: {e}") from e
        except sqlite3.DatabaseError as e:
            logger.error(
                f"Database error: {e}",
                extra={"db_path": str(self.db_path), "error_type": type(e).__name__}
            )
            raise IndexCorruptionError(f"Database error: {e}") from e
        except Exception as e:
            logger.error(
                f"Unexpected error accessing database: {e}",
                extra={
                    "db_path": str(self.db_path),
                    "error_type": type(e).__name__
                }
            )
            raise IndexCorruptionError(f"Unexpected database error: {e}") from e
        finally:
            if conn:
                conn.close()

    def check_integrity(self) -> bool:
        """
        Check database integrity using SQLite's built-in integrity check.

        Returns:
            True if database passes integrity check, False otherwise
        """
        try:
            with self.get_connection() as conn:
                result = conn.execute("PRAGMA integrity_check").fetchone()
                is_intact = result[0] == "ok"
                
                if not is_intact:
                    logger.warning(
                        f"Database integrity check failed: {result[0]}",
                        extra={"db_path": str(self.db_path)}
                    )
                
                return is_intact
        except IndexCorruptionError:
            # Already logged in get_connection
            return False
        except Exception as e:
            logger.error(
                f"Unexpected error during integrity check: {e}",
                extra={
                    "db_path": str(self.db_path),
                    "error_type": type(e).__name__
                }
            )
            return False

    def rebuild_if_corrupted(self) -> bool:
        """
        Check database integrity and rebuild if corrupted.
        
        Attempts to preserve data integrity by only rebuilding
        when absolutely necessary.

        Returns:
            True if database is healthy or was successfully rebuilt,
            False if rebuild failed
        """
        if self.check_integrity():
            return True
            
        logger.warning(
            "Database corruption detected, attempting rebuild",
            extra={"db_path": str(self.db_path)}
        )
        
        try:
            # Remove corrupted database and all related files
            self._remove_database_files()
            
            # Recreate schema
            self._create_schema()
            
            logger.info(
                "Database rebuilt successfully",
                extra={"db_path": str(self.db_path)}
            )
            return True
            
        except OSError as e:
            logger.error(
                f"Failed to remove corrupted database: {e}",
                extra={
                    "db_path": str(self.db_path),
                    "error_type": type(e).__name__
                }
            )
            return False
        except IndexCorruptionError as e:
            # Already logged in _create_schema
            return False
        except Exception as e:
            logger.error(
                f"Unexpected error rebuilding database: {e}",
                extra={
                    "db_path": str(self.db_path),
                    "error_type": type(e).__name__
                }
            )
            return False
