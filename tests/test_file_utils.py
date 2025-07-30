"""Tests for file utilities."""
from pathlib import Path

import pytest

from src.file_utils import (
    detect_encoding,
    get_file_stats,
    has_text_extension,
    is_text_file,
    is_within_size_limit,
    read_text_file,
)


class TestFileTypeDetection:
    """Test file type detection functionality."""

    def test_has_text_extension(self):
        """Test text extension detection."""
        # Text files
        assert has_text_extension(Path("file.txt"))
        assert has_text_extension(Path("README.md"))
        assert has_text_extension(Path("script.py"))
        assert has_text_extension(Path("config.json"))

        # Non-text files
        assert not has_text_extension(Path("image.jpg"))
        assert not has_text_extension(Path("video.mp4"))
        assert not has_text_extension(Path("archive.zip"))
        assert not has_text_extension(Path("noextension"))

    def test_is_text_file_by_extension(self, temp_dir):
        """Test text file detection by extension only."""
        text_file = temp_dir / "test.txt"
        text_file.write_text("Hello")

        binary_file = temp_dir / "test.jpg"
        binary_file.write_bytes(b"fake image data")

        assert is_text_file(text_file, check_content=False)
        assert not is_text_file(binary_file, check_content=False)

    def test_is_text_file_by_content(self, temp_dir):
        """Test text file detection by content."""
        # Text file with text extension
        text_file = temp_dir / "test.txt"
        text_file.write_text("This is text content")
        assert is_text_file(text_file)

        # Binary file with text extension (should detect as binary)
        binary_with_text_ext = temp_dir / "fake.txt"
        binary_with_text_ext.write_bytes(b'\x00\x01\x02\x03')
        assert not is_text_file(binary_with_text_ext)

        # ZIP file signature
        zip_file = temp_dir / "test.txt"
        zip_file.write_bytes(b'PK\x03\x04' + b'some data')
        assert not is_text_file(zip_file)

        # PDF signature
        pdf_file = temp_dir / "test.txt"
        pdf_file.write_bytes(b'%PDF-1.4' + b'some data')
        assert not is_text_file(pdf_file)


class TestEncodingDetection:
    """Test file encoding detection."""

    def test_detect_utf8_encoding(self, temp_dir):
        """Test UTF-8 encoding detection."""
        utf8_file = temp_dir / "utf8.txt"
        utf8_file.write_text("Hello 世界", encoding='utf-8')

        encoding, error = detect_encoding(utf8_file)
        assert encoding == 'utf-8'
        assert error is None

    def test_detect_utf8_bom_encoding(self, temp_dir):
        """Test UTF-8 with BOM encoding detection."""
        utf8_bom_file = temp_dir / "utf8_bom.txt"
        utf8_bom_file.write_text("Hello", encoding='utf-8-sig')

        encoding, error = detect_encoding(utf8_bom_file)
        assert encoding == 'utf-8-sig'
        assert error is None

    def test_detect_latin1_encoding(self, temp_dir):
        """Test Latin-1 encoding detection."""
        latin1_file = temp_dir / "latin1.txt"
        latin1_file.write_bytes("Café résumé".encode('latin-1'))

        encoding, error = detect_encoding(latin1_file)
        assert encoding == 'latin-1'
        assert error is None

    def test_detect_encoding_failure(self, temp_dir: Path) -> None:
        """
        Test encoding detection with binary data.
        
        Verifies that latin-1 is returned as fallback encoding
        since it can decode any byte sequence.
        """
        # Create a file with arbitrary bytes
        bad_file = temp_dir / "bad.txt"
        bad_file.write_bytes(b'\xff\xfe\xfd\xfc')

        encoding, error = detect_encoding(bad_file)
        
        # latin-1 can decode any byte sequence, so it will succeed
        assert encoding == 'latin-1'
        assert error is None


class TestFileReading:
    """Test file reading functionality."""

    def test_read_text_file_auto_encoding(self, temp_dir):
        """Test reading file with auto-detected encoding."""
        text_file = temp_dir / "test.txt"
        content = "Hello, world! 你好"
        text_file.write_text(content, encoding='utf-8')

        read_content, error = read_text_file(text_file)
        assert read_content == content
        assert error is None

    def test_read_text_file_specific_encoding(self, temp_dir):
        """Test reading file with specific encoding."""
        text_file = temp_dir / "test.txt"
        content = "Café"
        text_file.write_bytes(content.encode('latin-1'))

        read_content, error = read_text_file(text_file, encoding='latin-1')
        assert read_content == content
        assert error is None

    def test_read_text_file_wrong_encoding(self, temp_dir):
        """Test reading file with wrong encoding."""
        text_file = temp_dir / "test.txt"
        text_file.write_bytes("Café".encode('latin-1'))

        read_content, error = read_text_file(text_file, encoding='ascii')
        assert read_content is None
        assert "Failed to read file" in error

    def test_read_nonexistent_file(self, temp_dir):
        """Test reading non-existent file."""
        nonexistent = temp_dir / "nonexistent.txt"

        read_content, error = read_text_file(nonexistent)
        assert read_content is None
        assert error is not None


class TestFileStats:
    """Test file statistics functions."""

    def test_get_file_stats(self, temp_dir):
        """Test getting file size and modification time."""
        test_file = temp_dir / "test.txt"
        content = "Hello, world!"
        test_file.write_text(content)

        size, mtime = get_file_stats(test_file)

        assert size == len(content)
        assert mtime > 0
        assert isinstance(mtime, float)

    def test_is_within_size_limit(self, temp_dir):
        """Test file size limit checking."""
        # Small file
        small_file = temp_dir / "small.txt"
        small_file.write_text("Small content")
        assert is_within_size_limit(small_file, 1.0)  # 1 MB limit

        # Large file
        large_file = temp_dir / "large.txt"
        large_file.write_text("X" * (2 * 1024 * 1024))  # 2 MB
        assert not is_within_size_limit(large_file, 1.0)  # 1 MB limit
        assert is_within_size_limit(large_file, 3.0)  # 3 MB limit

    def test_is_within_size_limit_nonexistent(self, temp_dir):
        """Test size limit check for non-existent file."""
        nonexistent = temp_dir / "nonexistent.txt"
        assert not is_within_size_limit(nonexistent, 10.0)
