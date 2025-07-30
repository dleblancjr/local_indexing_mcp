#!/usr/bin/env python
"""Simple test runner script for the local indexing MCP project."""
import subprocess
import sys
from pathlib import Path


def main():
    """Run all tests with coverage reporting."""
    project_root = Path(__file__).parent.parent

    # Ensure we're in the project root
    import os
    os.chdir(project_root)

    print("Running tests for Local Indexing MCP Server...")
    print("-" * 60)

    # Run pytest with coverage
    cmd = [
        sys.executable, "-m", "pytest",
        "-v",  # Verbose output
        "--cov=src",  # Coverage for src directory
        "--cov-report=term-missing",  # Show missing lines
        "--cov-report=html",  # Generate HTML report
        "tests/"  # Test directory
    ]

    try:
        result = subprocess.run(cmd, check=True)
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print(f"📊 Coverage report generated in: {project_root / 'htmlcov' / 'index.html'}")
        return 0
    except subprocess.CalledProcessError as e:
        print("\n" + "=" * 60)
        print("❌ Some tests failed!")
        return e.returncode
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
