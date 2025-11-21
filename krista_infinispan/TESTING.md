# Testing Guide

This guide explains how to run tests for the Krista Infinispan project, with instructions for both traditional pip/venv workflows and the modern uv tool.

## Prerequisites

- Python 3.8 or higher
- Git (for cloning the repository)

## Method 1: Using uv (Recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package installer and resolver, written in Rust.

### Install uv

```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip
pip install uv
```

### Setup and Run Tests

```bash
# Clone the repository
git clone <repository-url>
cd krista-infinispan

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install the package and dependencies
uv pip install -e .
uv pip install -r requirements.txt

# Run tests
pytest
```

### Quick Test Commands with uv

```bash
# Run all tests with verbose output
uv run pytest -v

# Run tests with coverage
uv run pytest --cov=krista_infinispan --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_cache_operations.py

# Run tests by marker
uv run pytest -m "not slow"

# Run tests in parallel
uv run pytest -n auto
```

## Method 2: Using pip and venv

### Setup Virtual Environment

```bash
# Clone the repository
git clone <repository-url>
cd krista-infinispan

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install the package and dependencies
pip install -e .
pip install -r requirements.txt
```

### Run Tests

```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run tests with coverage
pytest --cov=krista_infinispan --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=krista_infinispan --cov-report=html
```

## Test Commands Reference

### Basic Test Execution

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Stop on first failure
pytest -x

# Show print statements
pytest -s
```

### Running Specific Tests

```bash
# Run specific test file
pytest tests/test_cache_operations.py

# Run specific test class
pytest tests/test_cache_operations.py::TestCacheOperations

# Run specific test method
pytest tests/test_cache_operations.py::TestCacheOperations::test_put_and_get_string

# Run tests matching pattern
pytest -k "test_put"
```

### Using Test Markers

The project defines several test markers in `pytest.ini`:

```bash
# Run only fast tests (exclude slow tests)
pytest -m "not slow"

# Run only integration tests
pytest -m "integration"

# Run only performance tests
pytest -m "performance"

# Combine markers
pytest -m "integration and not slow"
```

### Coverage Reports

```bash
# Terminal coverage report
pytest --cov=krista_infinispan --cov-report=term-missing

# HTML coverage report (opens in browser)
pytest --cov=krista_infinispan --cov-report=html
open htmlcov/index.html  # On macOS
xdg-open htmlcov/index.html  # On Linux
start htmlcov/index.html  # On Windows

# XML coverage report (for CI)
pytest --cov=krista_infinispan --cov-report=xml
```

### Parallel Test Execution

```bash
# Install pytest-xdist for parallel execution
pip install pytest-xdist  # or: uv pip install pytest-xdist

# Run tests in parallel (auto-detect CPU cores)
pytest -n auto

# Run tests on specific number of cores
pytest -n 4
```

### Debugging Tests

```bash
# Drop into debugger on failure
pytest --pdb

# Drop into debugger on first failure
pytest --pdb -x

# Show local variables in tracebacks
pytest --tb=long -v

# Short traceback format
pytest --tb=short
```

## Test Structure

```
krista-infinispan/
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Shared fixtures and configuration
│   ├── test_cache_config.py     # Configuration tests
│   ├── test_cache_creator.py    # Cache creation tests
│   ├── test_cache_operations.py # Cache operation tests
│   ├── test_integration.py      # Integration tests
│   └── test_performance.py      # Performance tests
├── pytest.ini                  # Pytest configuration
├── requirements.txt             # All dependencies
└── TESTING.md                   # This file
```

## Continuous Testing During Development

### Using pytest-watch

```bash
# Install pytest-watch
pip install pytest-watch  # or: uv pip install pytest-watch

# Watch for changes and re-run tests
ptw
```

### Using pytest with looponfail

```bash
# Re-run tests when files change
pytest --looponfail
```

## Environment Variables

Some tests may require environment variables:

```bash
# Set test environment variables
export INFINISPAN_HOST=localhost
export INFINISPAN_PORT=11222
export INFINISPAN_USERNAME=admin
export INFINISPAN_PASSWORD=admin

# Then run tests
pytest
```

## Quick Setup Scripts

### For uv users

Create `test-setup-uv.sh`:

```bash
#!/bin/bash
echo "Setting up test environment with uv..."
uv venv
source .venv/bin/activate
uv pip install -e .
uv pip install -r requirements.txt
echo "Setup complete! Run 'pytest' to execute tests."
```

### For pip users

Create `test-setup-pip.sh`:

```bash
#!/bin/bash
echo "Setting up test environment with pip..."
python -m venv venv
source venv/bin/activate
pip install -e .
pip install -r requirements.txt
echo "Setup complete! Run 'pytest' to execute tests."
```

Make scripts executable:
```bash
chmod +x test-setup-uv.sh test-setup-pip.sh
```

## Common Issues and Solutions

### Import Errors
```bash
# Ensure package is installed in development mode
pip install -e .  # or: uv pip install -e .
```

### Missing Dependencies
```bash
# Install all requirements
pip install -r requirements.txt  # or: uv pip install -r requirements.txt
```

### Permission Issues (Windows)
```bash
# Run as administrator or use:
python -m pytest
```

### Virtual Environment Issues
```bash
# Deactivate and recreate virtual environment
deactivate
rm -rf venv  # or .venv for uv
# Then recreate following setup steps above
```

## CI/CD Integration

For continuous integration, use:

```bash
# Install dependencies
pip install -e .
pip install -r requirements.txt

# Run tests with coverage and XML output
pytest --cov=krista_infinispan --cov-report=xml --cov-report=term-missing

# The coverage.xml file can be uploaded to coverage services
```

## Performance Testing

```bash
# Run only performance tests
pytest -m performance

# Run performance tests with detailed output
pytest -m performance -v -s

# Generate performance reports
pytest -m performance --benchmark-only
```

## Test Configuration

The `pytest.ini` file contains project-specific test configuration:

- Test discovery patterns
- Default command-line options
- Custom markers
- Warning filters

You can override these settings by passing command-line arguments to pytest.