#!/usr/bin/env python
"""Script to remove whitespace from blank lines in all Python files."""
import os
from pathlib import Path


def clean_blank_lines(filepath):
    """Remove whitespace from blank lines in a Python file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    modified = False
    cleaned_lines = []

    for line in lines:
        # If line contains only whitespace, make it truly empty
        if line.strip() == '' and line != '\n' and line != '':
            cleaned_lines.append('\n')
            modified = True
        else:
            cleaned_lines.append(line)

    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(cleaned_lines)
        return True
    return False


def process_directory(root_dir):
    """Process all Python files in the directory tree."""
    root_path = Path(root_dir)
    modified_files = []

    # Find all Python files
    python_files = []
    for ext in ['*.py']:
        python_files.extend(root_path.rglob(ext))

    # Process each file
    for py_file in python_files:
        # Skip virtual environment and cache directories
        if any(part in py_file.parts for part in ['.venv', '__pycache__', '.git']):
            continue

        if clean_blank_lines(py_file):
            modified_files.append(py_file)
            print(f"✓ Cleaned: {py_file.relative_to(root_path)}")

    return modified_files


def main():
    """Main function."""
    project_root = Path(__file__).parent.parent

    print("Cleaning whitespace from blank lines in Python files...")
    print("=" * 60)

    modified = process_directory(project_root)

    print("\n" + "=" * 60)
    if modified:
        print(f"✅ Cleaned {len(modified)} files")
    else:
        print("✅ All files already clean - no whitespace on blank lines found")


if __name__ == "__main__":
    main()
