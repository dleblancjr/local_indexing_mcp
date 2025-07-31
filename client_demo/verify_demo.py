#!/usr/bin/env python3
"""
Demo verification script for Local Indexing MCP Server.

This script checks that all demo components are properly set up
before running the main demo.
"""

import json
import sys
from pathlib import Path


def check_demo_config():
    """Check that the demo configuration is valid."""
    config_path = Path("client_demo/demo_config.json")
    
    if not config_path.exists():
        return False, "Demo config file not found"
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        required_fields = ['source_directory', 'index_output_directory']
        for field in required_fields:
            if field not in config:
                return False, f"Missing required field: {field}"
        
        # Check that source directory exists
        source_dir = Path(config['source_directory'])
        if not source_dir.exists():
            return False, f"Source directory does not exist: {source_dir}"
        
        return True, "Demo configuration is valid"
        
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON in config: {e}"
    except Exception as e:
        return False, f"Error reading config: {e}"


def check_sample_documents():
    """Check that sample documents exist."""
    docs_dir = Path("client_demo/sample_documents")
    
    if not docs_dir.exists():
        return False, "Sample documents directory not found"
    
    expected_files = [
        "README.md",
        "python_tutorial.txt", 
        "machine_learning.md",
        "sample_code.py"
    ]
    
    missing_files = []
    for filename in expected_files:
        if not (docs_dir / filename).exists():
            missing_files.append(filename)
    
    if missing_files:
        return False, f"Missing sample files: {missing_files}"
    
    return True, f"All {len(expected_files)} sample documents found"


def check_main_server():
    """Check that the main MCP server is accessible."""
    main_py = Path("main.py")
    
    if not main_py.exists():
        return False, "main.py not found (run from project root)"
    
    return True, "MCP server main.py found"


def check_python_version():
    """Check Python version compatibility."""
    if sys.version_info < (3, 8):
        return False, f"Python 3.8+ required, found {sys.version}"
    
    return True, f"Python version OK: {sys.version}"


def main():
    """Run all verification checks."""
    print("🔍 Verifying Local Indexing MCP Demo Setup")
    print("=" * 50)
    
    checks = [
        ("Python Version", check_python_version),
        ("Demo Configuration", check_demo_config),
        ("Sample Documents", check_sample_documents),
        ("MCP Server", check_main_server),
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        try:
            passed, message = check_func()
            status = "✅" if passed else "❌"
            print(f"{status} {check_name}: {message}")
            
            if not passed:
                all_passed = False
                
        except Exception as e:
            print(f"❌ {check_name}: Error during check - {e}")
            all_passed = False
    
    print("\n" + "=" * 50)
    
    if all_passed:
        print("🎉 All checks passed! Demo is ready to run.")
        print("\nTo run the demo:")
        print("  python client_demo/simple_demo.py")
    else:
        print("⚠️  Some checks failed. Please fix the issues above before running the demo.")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())