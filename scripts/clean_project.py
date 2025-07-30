#!/usr/bin/env python
"""Cross-platform project cleaning script."""
import shutil
import sys
from pathlib import Path


def remove_path(path: Path, description: str) -> None:
    """Remove a file or directory safely."""
    try:
        if path.exists():
            if path.is_file():
                path.unlink()
                print(f"✅ Removed {description}: {path}")
            elif path.is_dir():
                shutil.rmtree(path)
                print(f"✅ Removed {description}: {path}")
        else:
            print(f"⚪ {description} not found: {path}")
    except Exception as e:
        print(f"❌ Failed to remove {description} {path}: {e}")


def find_and_remove_pattern(root: Path, pattern: str, description: str) -> None:
    """Find and remove files/directories matching a pattern."""
    count = 0
    for path in root.rglob(pattern):
        try:
            if path.is_file():
                path.unlink()
                count += 1
            elif path.is_dir():
                shutil.rmtree(path)
                count += 1
        except Exception as e:
            print(f"❌ Failed to remove {path}: {e}")
    
    if count > 0:
        print(f"✅ Removed {count} {description}")
    else:
        print(f"⚪ No {description} found")


def main():
    """Clean all temporary and cache files."""
    project_root = Path(__file__).parent.parent
    
    print("Cleaning Local Indexing MCP Server project...")
    print("=" * 50)
    
    # Clean Python cache files and directories
    find_and_remove_pattern(project_root, "__pycache__", "Python cache directories")
    find_and_remove_pattern(project_root, "*.pyc", "Python compiled files (.pyc)")
    find_and_remove_pattern(project_root, "*.pyo", "Python optimized files (.pyo)")
    
    # Clean coverage files
    remove_path(project_root / ".coverage", ".coverage file")
    remove_path(project_root / "htmlcov", "HTML coverage report directory")
    
    # Clean test cache
    remove_path(project_root / ".pytest_cache", "pytest cache directory")
    
    # Clean linting/type checking cache
    remove_path(project_root / ".mypy_cache", "MyPy cache directory")
    remove_path(project_root / ".ruff_cache", "Ruff cache directory")
    
    # Clean project-specific directories
    remove_path(project_root / "indexes", "indexes directory")
    
    # Clean additional Python/IDE cache directories if they exist
    remove_path(project_root / ".vscode", "VS Code settings")
    remove_path(project_root / ".idea", "IntelliJ IDEA settings")
    find_and_remove_pattern(project_root, "*.egg-info", "egg-info directories")
    
    print("\n" + "=" * 50)
    print("🎉 Project cleaning complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
