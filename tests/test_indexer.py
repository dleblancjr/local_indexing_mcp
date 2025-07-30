"""Tests for file indexing functionality."""
import os
import time
from pathlib import Path
from typing import Dict, Tuple

import pytest

from src.database import Database
from src.indexer import FileIndexer
from src.models import ServerConfig


class TestFileIndexer:
    """Test file indexing operations."""

    @pytest.fixture
    def indexer_with_files(self, sample_config, test_database, sample_text_files):
        """Create indexer with sample files."""
        indexer = FileIndexer(sample_config, test_database)
        return indexer, sample_text_files

    def test_scan_directory(self, indexer_with_files):
        """Test directory scanning."""
        indexer, files = indexer_with_files

        scanned_files = indexer.scan_directory()
        scanned_paths = {f.name for f in scanned_files}

        # Should find text files
        assert 'simple.txt' in scanned_paths
        assert 'document.md' in scanned_paths
        assert 'nested.txt' in scanned_paths

        # Should not find binary file
        assert 'binary.bin' not in scanned_paths

    def test_scan_directory_excludes_index(self, sample_config, test_database):
        """Test that index directory is excluded from scanning."""
        # Create a file in the index directory
        index_dir = Path(sample_config['index_output_directory'])
        index_dir.mkdir(exist_ok=True)
        (index_dir / 'should_not_index.txt').write_text('This should not be indexed')

        indexer = FileIndexer(sample_config, test_database)
        scanned_files = indexer.scan_directory()

        # Should not include files from index directory
        for file in scanned_files:
            assert str(index_dir) not in str(file)

    def test_extension_filtering(self, sample_config, test_database, temp_dir):
        """Test file extension filtering."""
        source_dir = Path(sample_config['source_directory'])

        # Create files with various extensions
        (source_dir / 'included.txt').write_text('text')
        (source_dir / 'included.md').write_text('markdown')
        (source_dir / 'excluded.py').write_text('python')
        (source_dir / 'excluded.java').write_text('java')

        # Test with included extensions
        indexer = FileIndexer(sample_config, test_database)
        files = indexer.scan_directory()
        names = {f.name for f in files}

        assert 'included.txt' in names
        assert 'included.md' in names
        assert 'excluded.py' not in names
        assert 'excluded.java' not in names

        # Test with excluded extensions
        sample_config['included_extensions'] = []  # Include all
        sample_config['excluded_extensions'] = ['.py', '.java']

        indexer2 = FileIndexer(sample_config, test_database)
        files2 = indexer2.scan_directory()
        names2 = {f.name for f in files2}

        assert 'included.txt' in names2
        assert 'included.md' in names2
        assert 'excluded.py' not in names2
        assert 'excluded.java' not in names2

    def test_size_limit_filtering(self, sample_config, test_database, sample_text_files):
        """Test file size limit filtering."""
        # Set a low size limit
        sample_config['max_file_size_mb'] = 0.001  # 1KB

        indexer = FileIndexer(sample_config, test_database)
        files = indexer.scan_directory()
        names = {f.name for f in files}

        # Large file should be excluded
        assert 'large.txt' not in names
        # Small files should be included
        assert 'simple.txt' in names

    def test_get_changed_files_new(self, indexer_with_files):
        """Test detection of new files."""
        indexer, files = indexer_with_files

        all_files = [files['simple'], files['markdown']]
        changed = indexer.get_changed_files(all_files)

        # All files should be new
        assert len(changed) == len(all_files)

    def test_get_changed_files_modified(self, indexer_with_files):
        """Test detection of modified files."""
        indexer, files = indexer_with_files

        # Index a file first
        indexer.index_file(files['simple'])

        # Wait a bit and modify the file
        time.sleep(0.1)
        files['simple'].write_text('Modified content')

        # Should detect as changed
        changed = indexer.get_changed_files([files['simple']])
        assert len(changed) == 1
        assert changed[0] == files['simple']

    def test_get_changed_files_unchanged(self, indexer_with_files):
        """Test that unchanged files are not detected as changed."""
        indexer, files = indexer_with_files

        # Index a file
        indexer.index_file(files['simple'])

        # Without modification, should not be detected as changed
        changed = indexer.get_changed_files([files['simple']])
        assert len(changed) == 0

    def test_index_file_success(self, indexer_with_files):
        """Test successful file indexing."""
        indexer, files = indexer_with_files

        result = indexer.index_file(files['simple'])
        assert result is True

        # Verify file was indexed
        with indexer.db.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM documents WHERE path = ?",
                (str(files['simple']),)
            ).fetchone()

            assert row is not None
            assert 'simple text file' in row['content']

    def test_index_file_binary(self, indexer_with_files):
        """Test that binary files are skipped."""
        indexer, files = indexer_with_files

        result = indexer.index_file(files['binary'])
        assert result is False

        # Verify file was not indexed
        with indexer.db.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM documents WHERE path = ?",
                (str(files['binary']),)
            ).fetchone()

            assert row is None

    def test_index_file_encoding_detection(self, indexer_with_files, temp_dir):
        """Test file encoding detection during indexing."""
        indexer, _ = indexer_with_files

        # Create file with specific encoding
        latin1_file = temp_dir / "source" / "latin1.txt"
        latin1_file.write_bytes("Café résumé".encode('latin-1'))

        result = indexer.index_file(latin1_file)
        assert result is True

        # Check encoding was saved
        with indexer.db.get_connection() as conn:
            row = conn.execute(
                "SELECT encoding FROM file_metadata WHERE path = ?",
                (str(latin1_file),)
            ).fetchone()

            assert row['encoding'] == 'latin-1'

    def test_index_file_error_handling(
        self, 
        indexer_with_files: Tuple[FileIndexer, Dict[str, Path]], 
        temp_dir: Path
    ) -> None:
        """
        Test error handling during file indexing.
        
        Verifies that binary files are properly rejected
        and not indexed in the database.
        """
        indexer, _ = indexer_with_files
        
        # Create a file with null bytes (binary content)
        bad_file = temp_dir / "source" / "bad_encoding.txt"
        bad_file.write_bytes(b'\x00\x01\x02\x03' * 100)
        
        # Attempt to index binary file
        result = indexer.index_file(bad_file)
        assert result is False
        
        # Verify file was not indexed
        with indexer.db.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM documents WHERE path = ?",
                (str(bad_file),)
            ).fetchone()
            
            # Binary files should be rejected
            assert row is None

    def test_remove_deleted_files(self, indexer_with_files):
        """Test removal of deleted files from index."""
        indexer, files = indexer_with_files

        # Index some files
        indexer.index_file(files['simple'])
        indexer.index_file(files['markdown'])

        # Simulate one file being deleted
        current_files = {files['markdown']}  # Only markdown remains

        removed_count = indexer.remove_deleted_files(current_files)
        assert removed_count == 1

        # Verify simple.txt was removed from index
        with indexer.db.get_connection() as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM documents WHERE path = ?",
                (str(files['simple']),)
            ).fetchone()[0]

            assert count == 0

    def test_refresh_index_full(self, indexer_with_files):
        """Test full index refresh."""
        indexer, files = indexer_with_files

        result = indexer.refresh_index()

        assert result['success'] is True
        assert result['files_processed'] > 0
        assert result['files_added'] >= 0
        assert result['files_updated'] >= 0
        assert result['files_removed'] >= 0
        assert result['duration_seconds'] >= 0
        assert len(result['errors']) == 0

        # Verify files were indexed
        with indexer.db.get_connection() as conn:
            count = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
            assert count > 0

    def test_refresh_index_specific_file(self, indexer_with_files):
        """Test refreshing a specific file."""
        indexer, files = indexer_with_files

        # Refresh specific file
        result = indexer.refresh_index(str(files['simple']))

        assert result['success'] is True
        assert result['files_processed'] == 1
        assert result['files_added'] == 1  # New file
        assert result['files_updated'] == 0
        assert result['files_removed'] == 0
        assert result['duration_seconds'] >= 0
        assert len(result['errors']) == 0

        # Verify file was indexed
        with indexer.db.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM documents WHERE path = ?",
                (str(files['simple']),)
            ).fetchone()

            assert row is not None

    def test_refresh_index_nonexistent_file(self, indexer_with_files):
        """Test refreshing non-existent file."""
        indexer, _ = indexer_with_files

        # Use a relative path that would be inside source directory but doesn't exist
        result = indexer.refresh_index("nonexistent_file.txt")

        assert result['success'] is False
        assert result['files_processed'] == 0
        assert result['files_added'] == 0
        assert result['files_updated'] == 0
        assert result['files_removed'] == 0
        assert result['duration_seconds'] >= 0
        assert len(result['errors']) == 1
        assert "not found" in result['errors'][0]

    def test_refresh_index_path_outside_source(self, indexer_with_files):
        """Test refreshing file with absolute path outside source directory."""
        indexer, _ = indexer_with_files

        # Use absolute path outside source directory to test security
        result = indexer.refresh_index("/nonexistent/file.txt")

        assert result['success'] is False
        assert result['files_processed'] == 0
        assert result['files_added'] == 0
        assert result['files_updated'] == 0
        assert result['files_removed'] == 0
        assert result['duration_seconds'] >= 0
        assert len(result['errors']) == 1
        assert "Path outside source directory" in result['errors'][0]

    def test_refresh_index_with_errors(self, indexer_with_files, temp_dir):
        """Test refresh with some files causing errors."""
        indexer, files = indexer_with_files

        # Create a problematic file
        bad_file = temp_dir / "source" / "bad.txt"
        bad_file.write_bytes(b'\x00' * 100)  # Binary content

        result = indexer.refresh_index()

        # Should process good files even if some fail
        assert result['files_processed'] > 0
        assert result['files_added'] >= 0
        assert result['files_updated'] >= 0
        assert result['files_removed'] >= 0
        assert result['duration_seconds'] >= 0
        # But success should be False due to errors
        assert result['success'] is False or len(result['errors']) > 0

    def test_validate_file_path_valid(self, indexer_with_files):
        """Test path validation with valid paths."""
        indexer, files = indexer_with_files

        # Test absolute path within source directory
        validated = indexer._validate_file_path(str(files['simple']))
        assert validated == files['simple']

        # Test relative path
        relative_path = files['simple'].name
        validated = indexer._validate_file_path(relative_path)
        assert validated.name == files['simple'].name

    def test_validate_file_path_invalid(self, indexer_with_files, temp_dir):
        """Test path validation with invalid paths."""
        indexer, _ = indexer_with_files

        # Create file outside source directory
        outside_file = temp_dir / "outside.txt"
        outside_file.write_text("outside content")

        # Should raise ValueError for path outside source directory
        with pytest.raises(ValueError, match="Path outside source directory"):
            indexer._validate_file_path(str(outside_file))

        # Test path traversal attempt
        with pytest.raises(ValueError, match="Path outside source directory"):
            indexer._validate_file_path("../../../etc/passwd")

    def test_refresh_index_force_parameter(self, indexer_with_files):
        """Test force refresh functionality."""
        indexer, files = indexer_with_files

        # First index some files
        result1 = indexer.refresh_index()
        initial_processed = result1['files_processed']
        assert result1['success'] is True
        assert initial_processed > 0

        # Normal refresh should process no files (no changes)
        result2 = indexer.refresh_index(force=False)
        assert result2['success'] is True
        assert result2['files_processed'] == 0  # No changes
        assert result2['files_updated'] == 0

        # Force refresh should process all files again
        result3 = indexer.refresh_index(force=True)
        assert result3['success'] is True
        assert result3['files_processed'] == initial_processed
        assert result3['files_updated'] == initial_processed  # All should be updates
        assert result3['files_added'] == 0  # None should be new

    def test_refresh_index_file_statistics(self, indexer_with_files):
        """Test detailed file statistics tracking."""
        indexer, files = indexer_with_files

        # First refresh - all files should be added
        result1 = indexer.refresh_index()
        assert result1['success'] is True
        assert result1['files_added'] > 0
        assert result1['files_updated'] == 0
        assert result1['files_removed'] == 0
        assert result1['files_processed'] == result1['files_added']

        # Modify a file
        files['simple'].write_text('Modified content')
        time.sleep(0.1)  # Ensure timestamp changes

        # Second refresh - modified file should be updated
        result2 = indexer.refresh_index()
        assert result2['success'] is True
        assert result2['files_added'] == 0
        assert result2['files_updated'] == 1
        assert result2['files_removed'] == 0
        assert result2['files_processed'] == 1

        # Delete a file and refresh
        files['simple'].unlink()
        result3 = indexer.refresh_index()
        assert result3['success'] is True
        assert result3['files_added'] == 0
        assert result3['files_updated'] == 0
        assert result3['files_removed'] == 1
        assert result3['files_processed'] == 0  # No files to process

    def test_refresh_index_specific_file_path_validation(self, indexer_with_files, temp_dir):
        """Test path validation in specific file refresh."""
        indexer, _ = indexer_with_files

        # Create file outside source directory
        outside_file = temp_dir / "outside.txt"
        outside_file.write_text("outside content")

        # Should fail with path validation error
        result = indexer.refresh_index(str(outside_file))
        assert result['success'] is False
        assert result['files_processed'] == 0
        assert result['files_added'] == 0
        assert result['files_updated'] == 0
        assert result['files_removed'] == 0
        assert len(result['errors']) == 1
        assert "Path outside source directory" in result['errors'][0]

    def test_refresh_index_timing(self, indexer_with_files):
        """Test that timing information is properly recorded."""
        indexer, files = indexer_with_files

        start_time = time.time()
        result = indexer.refresh_index()
        end_time = time.time()

        # Duration should be reasonable
        assert result['duration_seconds'] >= 0
        assert result['duration_seconds'] <= (end_time - start_time + 1)  # Allow some margin
        assert isinstance(result['duration_seconds'], float)

    def test_create_result_helper(self, indexer_with_files):
        """Test the _create_result helper method."""
        indexer, _ = indexer_with_files

        start_time = time.time()
        time.sleep(0.01)  # Small delay to ensure non-zero duration

        result = indexer._create_result(
            start_time=start_time,
            success=True,
            files_processed=5,
            files_added=3,
            files_updated=2,
            files_removed=1,
            errors=["test error"]
        )

        assert result['success'] is True
        assert result['files_processed'] == 5
        assert result['files_added'] == 3
        assert result['files_updated'] == 2
        assert result['files_removed'] == 1
        assert result['duration_seconds'] > 0
        assert result['errors'] == ["test error"]
        assert isinstance(result['duration_seconds'], float)
