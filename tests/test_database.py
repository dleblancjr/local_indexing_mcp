"""Tests for database operations."""
import sqlite3
from pathlib import Path

import pytest

from src.database import Database
from src.exceptions import IndexCorruptionError


class TestDatabaseInitialization:
    """Test database initialization and schema creation."""

    def test_database_creation(self, temp_dir):
        """Test that database is created with proper schema."""
        db_path = temp_dir / "test.db"
        db = Database(db_path)

        assert db_path.exists()

        # Verify schema
        with db.get_connection() as conn:
            # Check tables exist
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = {row[0] for row in cursor}
            assert 'file_metadata' in tables

            # Check virtual table
            cursor = conn.execute(
                "SELECT sql FROM sqlite_master WHERE name='documents'"
            )
            create_sql = cursor.fetchone()[0]
            assert 'fts5' in create_sql.lower()
            assert 'tokenize' in create_sql.lower()

    def test_database_pragmas(self, temp_dir):
        """Test that performance pragmas are set."""
        db_path = temp_dir / "test.db"
        db = Database(db_path)
        
        with db.get_connection() as conn:
            # Check journal mode
            journal_mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
            assert journal_mode == 'wal'
            
            # Check synchronous mode (NORMAL = 1 or FULL = 2 are both acceptable)
            sync_mode = conn.execute("PRAGMA synchronous").fetchone()[0]
            assert sync_mode in [1, 2]  # NORMAL or FULL


class TestDatabaseConnection:
    """Test database connection management."""

    def test_connection_context_manager(self, test_database):
        """Test that connection context manager works properly."""
        # Test successful operation
        with test_database.get_connection() as conn:
            assert conn is not None
            assert isinstance(conn, sqlite3.Connection)

            # Test that we can execute queries
            cursor = conn.execute("SELECT 1")
            assert cursor.fetchone()[0] == 1

    def test_connection_row_factory(self, test_database):
        """Test that Row factory is set for connections."""
        with test_database.get_connection() as conn:
            conn.execute(
                "INSERT INTO file_metadata VALUES (?, ?, ?, ?, ?, ?)",
                ('/test/path', 100, 1234567890.0, 1234567890.0, 'utf-8', None)
            )

            row = conn.execute(
                "SELECT * FROM file_metadata WHERE path = ?",
                ('/test/path',)
            ).fetchone()

            # Test Row access
            assert row['path'] == '/test/path'
            assert row['size'] == 100
            assert row['encoding'] == 'utf-8'

    def test_connection_error_handling(self, temp_dir):
        """Test error handling for database connection issues."""
        # Try to create database in read-only directory
        db_path = temp_dir / "readonly" / "test.db"
        db_path.parent.mkdir()

        # This should work (creates directory and database)
        db = Database(db_path)

        # Now make it read-only and try to write
        db_path.chmod(0o444)

        with pytest.raises(IndexCorruptionError):
            with db.get_connection() as conn:
                conn.execute("INSERT INTO file_metadata VALUES (?, ?, ?, ?, ?, ?)",
                           ('test', 1, 1, 1, 'utf-8', None))


class TestDatabaseIntegrity:
    """Test database integrity checking and recovery."""

    def test_check_integrity_healthy(self, test_database):
        """Test integrity check on healthy database."""
        assert test_database.check_integrity() is True

    def test_check_integrity_corrupted(self, temp_dir):
        """Test integrity check on corrupted database."""
        db_path = temp_dir / "corrupted.db"
        
        # Create a corrupted database by writing garbage
        db_path.write_bytes(b'This is not a valid SQLite database!')
        
        # Database constructor should handle corruption by rebuilding
        db = Database(db_path)
        # After rebuild, database should exist and be valid
        assert db_path.exists()
        assert db.check_integrity() is True

    def test_rebuild_if_corrupted(self, temp_dir):
        """Test database rebuild functionality."""
        db_path = temp_dir / "test.db"
        db = Database(db_path)

        # Insert some data
        with db.get_connection() as conn:
            conn.execute(
                "INSERT INTO file_metadata VALUES (?, ?, ?, ?, ?, ?)",
                ('/test/path', 100, 1234567890.0, 1234567890.0, 'utf-8', None)
            )
            conn.commit()

        # Corrupt the database
        db_path.write_bytes(b'Corrupted data!')

        # Try to rebuild
        result = db.rebuild_if_corrupted()
        assert result is True

        # Database should be fresh (no data)
        with db.get_connection() as conn:
            count = conn.execute("SELECT COUNT(*) FROM file_metadata").fetchone()[0]
            assert count == 0


class TestDatabaseOperations:
    """Test database operations with FTS5."""

    def test_fts5_insert_and_search(self, test_database):
        """Test FTS5 insert and search operations."""
        with test_database.get_connection() as conn:
            # Insert document
            conn.execute(
                "INSERT INTO documents (path, content, last_modified) VALUES (?, ?, ?)",
                ('/test/doc1.txt', 'This is a test document about Python programming', '2024-01-01T00:00:00')
            )
            conn.commit()

            # Search for content
            cursor = conn.execute(
                "SELECT path, snippet(documents, 1, '<b>', '</b>', '...', 10) as snippet "
                "FROM documents WHERE documents MATCH ?",
                ('Python',)
            )

            result = cursor.fetchone()
            assert result is not None
            assert result['path'] == '/test/doc1.txt'
            assert 'Python' in result['snippet']

    def test_fts5_ranking(self, test_database):
        """Test FTS5 BM25 ranking."""
        with test_database.get_connection() as conn:
            # Insert multiple documents
            docs = [
                ('/doc1.txt', 'Python is great', '2024-01-01T00:00:00'),
                ('/doc2.txt', 'Python Python Python', '2024-01-01T00:00:00'),
                ('/doc3.txt', 'I like programming', '2024-01-01T00:00:00'),
            ]

            for path, content, modified in docs:
                conn.execute(
                    "INSERT INTO documents VALUES (?, ?, ?)",
                    (path, content, modified)
                )
            conn.commit()

            # Search and check ranking
            cursor = conn.execute(
                "SELECT path, bm25(documents) as score "
                "FROM documents WHERE documents MATCH ? "
                "ORDER BY score",
                ('Python',)
            )

            results = cursor.fetchall()
            assert len(results) == 2
            # Document with more occurrences should rank higher (more negative score)
            assert results[0]['path'] == '/doc2.txt'
            assert results[1]['path'] == '/doc1.txt'
