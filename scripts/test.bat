@echo off
REM Windows batch file for running tests with coverage
REM Equivalent to test.sh for cross-platform compatibility

pytest --cov=src --cov-report=term-missing --cov-report=html tests/