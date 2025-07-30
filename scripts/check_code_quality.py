#!/usr/bin/env python
"""Code quality checking script for the local indexing MCP project."""
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and report results."""
    print(f"\n🔍 {description}...")
    print("-" * 40)

    try:
        result = subprocess.run(cmd, check=True)
        print(f"✅ {description} passed!")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ {description} failed!")
        return False
    except FileNotFoundError:
        print(f"⚠️  {cmd[0]} not found. Install with: pip install {cmd[0]}")
        return False


def main():
    """Run all code quality checks."""
    project_root = Path(__file__).parent.parent

    # Ensure we're in the project root
    import os
    os.chdir(project_root)

    print("Running code quality checks for Local Indexing MCP Server...")
    print("=" * 60)

    all_passed = True

    # Run black formatting check
    all_passed &= run_command(
        [sys.executable, "-m", "black", "--check", "src", "tests", "main.py"],
        "Black formatting check"
    )

    # Run ruff linting
    all_passed &= run_command(
        [sys.executable, "-m", "ruff", "check", "src", "tests", "main.py"],
        "Ruff linting"
    )

    # Run mypy type checking
    all_passed &= run_command(
        [sys.executable, "-m", "mypy", "src", "main.py", "scripts"],
        "MyPy type checking"
    )

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All code quality checks passed!")

        print("\n💡 To automatically fix formatting issues, run:")
        print(f"   python -m black src tests main.py")

        return 0
    else:
        print("❌ Some code quality checks failed!")

        print("\n💡 To fix issues:")
        print("   - Formatting: python -m black src tests main.py")
        print("   - Linting: python -m ruff check --fix src tests main.py")
        print("   - Type hints: Fix manually based on mypy output")

        return 1


if __name__ == "__main__":
    sys.exit(main())
