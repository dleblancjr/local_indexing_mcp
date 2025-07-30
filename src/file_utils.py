"""File type detection and encoding handling utilities."""
import logging
import os
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Common binary file signatures (magic numbers)
BINARY_SIGNATURES = [
    b'\x00\x00\x00',  # Null bytes
    b'\xff\xfe',      # UTF-16 BOM
    b'\xfe\xff',      # UTF-16 BOM
    b'\xff\xfe\x00\x00',  # UTF-32 BOM
    b'\x00\x00\xfe\xff',  # UTF-32 BOM
    b'PK\x03\x04',    # ZIP
    b'PK\x05\x06',    # ZIP
    b'PK\x07\x08',    # ZIP
    b'\x50\x4b\x03\x04',  # ZIP
    b'\x1f\x8b',      # GZIP
    b'BZh',           # BZIP2
    b'\x89PNG',       # PNG
    b'GIF87a',        # GIF
    b'GIF89a',        # GIF
    b'\xff\xd8\xff',  # JPEG
    b'ID3',           # MP3
    b'RIFF',          # WAV/AVI
    b'\x25\x50\x44\x46',  # PDF
]


def is_text_file(filepath: Path, check_content: bool = True) -> bool:
    """
    Determine if a file is a text file.

    Args:
        filepath: Path to the file
        check_content: Whether to check file content (slower but more accurate)

    Returns:
        True if file appears to be text, False otherwise
    """
    # First check extension
    if not has_text_extension(filepath):
        logger.debug(
            f"File rejected by extension check",
            extra={"filepath": str(filepath), "extension": filepath.suffix}
        )
        return False

    if not check_content:
        return True

    # Check file content
    try:
        with open(filepath, 'rb') as f:
            chunk = f.read(8192)  # Read first 8KB
            return _is_text_content(chunk, filepath)
            
    except OSError as e:
        logger.warning(
            f"Cannot read file for type detection: {e}",
            extra={"filepath": str(filepath), "error_type": type(e).__name__}
        )
        return False
    except Exception as e:
        logger.error(
            f"Unexpected error checking file type: {e}",
            extra={"filepath": str(filepath), "error_type": type(e).__name__}
        )
        return False


def _is_text_content(content: bytes, filepath: Path) -> bool:
    """
    Check if byte content appears to be text.
    
    Args:
        content: Byte content to check
        filepath: Path for logging context
        
    Returns:
        True if content appears to be text
    """
    # Check for binary signatures
    for sig in BINARY_SIGNATURES:
        if content.startswith(sig):
            logger.debug(
                f"Binary signature detected",
                extra={
                    "filepath": str(filepath),
                    "signature": sig[:4].hex()
                }
            )
            return False

    # Check for null bytes (common in binary files)
    if b'\x00' in content:
        logger.debug(
            f"Null bytes detected in file",
            extra={"filepath": str(filepath)}
        )
        return False

    # Try to decode as text
    try:
        content.decode('utf-8')
        return True
    except UnicodeDecodeError:
        # Try with latin-1 as fallback
        try:
            content.decode('latin-1')
            return True
        except UnicodeDecodeError:
            logger.debug(
                f"Failed to decode file as text",
                extra={"filepath": str(filepath)}
            )
            return False


def has_text_extension(filepath: Path) -> bool:
    """
    Check if file has a text file extension.

    Args:
        filepath: Path to check

    Returns:
        True if extension suggests text file
    """
    text_extensions = {
        '.txt', '.md', '.rst', '.log', '.csv', '.json', '.xml', '.html',
        '.htm', '.css', '.js', '.py', '.java', '.c', '.cpp', '.h', '.hpp',
        '.cs', '.rb', '.go', '.rs', '.php', '.sh', '.bat', '.ps1', '.yaml',
        '.yml', '.toml', '.ini', '.cfg', '.conf', '.properties'
    }
    return filepath.suffix.lower() in text_extensions


def detect_encoding(filepath: Path) -> Tuple[Optional[str], Optional[str]]:
    """
    Detect file encoding by trying common encodings.
    
    Checks for BOM markers first, then tries common encodings
    in order of likelihood.

    Args:
        filepath: Path to the file

    Returns:
        Tuple of (encoding, error_message)
        encoding is None if detection failed
    """
    # Check for UTF-8 BOM first
    try:
        with open(filepath, 'rb') as f:
            bom = f.read(3)
            if bom == b'\xef\xbb\xbf':
                logger.debug(
                    f"UTF-8 BOM detected",
                    extra={"filepath": str(filepath)}
                )
                return 'utf-8-sig', None
    except OSError as e:
        error_msg = f"Cannot read file for encoding detection: {e}"
        logger.warning(
            error_msg,
            extra={"filepath": str(filepath), "error_type": type(e).__name__}
        )
        return None, error_msg
    except Exception as e:
        error_msg = f"Unexpected error checking BOM: {e}"
        logger.error(
            error_msg,
            extra={"filepath": str(filepath), "error_type": type(e).__name__}
        )
        return None, error_msg

    # Try encodings in order
    encodings_to_try = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']

    for encoding in encodings_to_try:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                # Try to read first 1KB to validate encoding
                f.read(1024)
            
            logger.debug(
                f"Detected encoding: {encoding}",
                extra={"filepath": str(filepath)}
            )
            return encoding, None
            
        except UnicodeDecodeError:
            continue
        except OSError as e:
            error_msg = f"Cannot open file: {e}"
            logger.warning(
                error_msg,
                extra={
                    "filepath": str(filepath),
                    "encoding": encoding,
                    "error_type": type(e).__name__
                }
            )
            return None, error_msg
        except Exception as e:
            error_msg = f"Unexpected error with {encoding}: {e}"
            logger.error(
                error_msg,
                extra={
                    "filepath": str(filepath),
                    "encoding": encoding,
                    "error_type": type(e).__name__
                }
            )
            return None, error_msg

    logger.debug(
        f"Failed to detect encoding - tried all options",
        extra={"filepath": str(filepath), "encodings_tried": encodings_to_try}
    )
    return None, "Could not detect encoding"


def read_text_file(filepath: Path, encoding: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Read a text file with encoding detection.

    Args:
        filepath: Path to the file
        encoding: Encoding to use (auto-detected if None)

    Returns:
        Tuple of (content, error_message)
        content is None if read failed
    """
    if encoding is None:
        encoding, error = detect_encoding(filepath)
        if encoding is None:
            return None, f"Encoding detection failed: {error}"

    try:
        with open(filepath, 'r', encoding=encoding) as f:
            content = f.read()
        
        logger.debug(
            f"Successfully read file",
            extra={
                "filepath": str(filepath),
                "encoding": encoding,
                "size_bytes": len(content)
            }
        )
        return content, None
        
    except UnicodeDecodeError as e:
        error_msg = f"Failed to read file: {e}"
        logger.warning(
            error_msg,
            extra={
                "filepath": str(filepath),
                "encoding": encoding,
                "error_type": "UnicodeDecodeError"
            }
        )
        return None, error_msg
    except OSError as e:
        error_msg = f"Cannot read file: {e}"
        logger.warning(
            error_msg,
            extra={
                "filepath": str(filepath),
                "encoding": encoding,
                "error_type": type(e).__name__
            }
        )
        return None, error_msg
    except Exception as e:
        error_msg = f"Unexpected error reading file: {e}"
        logger.error(
            error_msg,
            extra={
                "filepath": str(filepath),
                "encoding": encoding,
                "error_type": type(e).__name__
            }
        )
        return None, error_msg


def get_file_stats(filepath: Path) -> Tuple[int, float]:
    """
    Get file size and modification time.

    Args:
        filepath: Path to the file

    Returns:
        Tuple of (size_in_bytes, mtime_as_float)

    Raises:
        OSError: If file cannot be accessed
    """
    stat = os.stat(filepath)
    return stat.st_size, stat.st_mtime


def is_within_size_limit(filepath: Path, max_size_mb: float) -> bool:
    """
    Check if file is within size limit.

    Args:
        filepath: Path to the file
        max_size_mb: Maximum size in megabytes

    Returns:
        True if file is within limit, False otherwise
        
    Note:
        Returns False for files that cannot be accessed
    """
    try:
        size_bytes = os.path.getsize(filepath)
        size_mb = size_bytes / (1024 * 1024)
        is_within = size_mb <= max_size_mb
        
        if not is_within:
            logger.debug(
                f"File exceeds size limit",
                extra={
                    "filepath": str(filepath),
                    "size_mb": round(size_mb, 2),
                    "limit_mb": max_size_mb
                }
            )
        
        return is_within
    except OSError as e:
        logger.warning(
            f"Cannot get file size: {e}",
            extra={
                "filepath": str(filepath),
                "error_type": type(e).__name__
            }
        )
        return False
