# Makefile for Local Indexing MCP Server

.PHONY: help install install-dev test coverage lint format clean run

# Default target
help:
	@echo "Local Indexing MCP Server - Development Commands"
	@echo "=============================================="
	@echo ""
	@echo "make install      Install production dependencies"
	@echo "make install-dev  Install development dependencies"
	@echo "make test         Run all tests"
	@echo "make coverage     Run tests with coverage report"
	@echo "make lint         Run code quality checks"
	@echo "make format       Auto-format code"
	@echo "make clean        Clean temporary files"
	@echo "make run          Run the MCP server"

# Install production dependencies
install:
	pip install -e .

# Install development dependencies
install-dev:
	pip install -e ".[dev]"

# Run tests
test:
	python -m pytest tests/ -v

# Run tests with coverage
coverage:
	python scripts/run_tests.py

# Run linting and type checking
lint:
	python scripts/check_code_quality.py

# Auto-format code
format:
	python -m black src tests main.py scripts
	python -m ruff check --fix src tests main.py scripts

# Clean temporary files
clean:
	python scripts/clean_project.py

# Run the server
run:
	python main.py
