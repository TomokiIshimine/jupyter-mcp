.PHONY: test test-basic test-deletion test-pytest install clean help

# Default target
help:
	@echo "Jupyter MCP Server - Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make test         - Run all tests"
	@echo "  make test-basic   - Run basic functionality test"
	@echo "  make test-deletion - Run deletion sync test"
	@echo "  make test-pytest  - Run tests with pytest"
	@echo "  make clean        - Clean test outputs and cache"
	@echo "  make jupyter      - Start Jupyter server (for testing)"

# Install dependencies
install:
	pip install -r requirements.txt
	pip install pytest pytest-asyncio

# Run all tests
test:
	./run_tests.sh

# Run basic functionality test
test-basic:
	./run_tests.sh basic

# Run deletion sync test
test-deletion:
	./run_tests.sh deletion

# Run tests with pytest
test-pytest:
	./run_tests.sh pytest

# Clean test outputs and cache
clean:
	rm -rf test_output/
	rm -rf test_images/
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf src/__pycache__/
	rm -rf tests/__pycache__/
	find . -name "*.pyc" -delete
	find . -name ".DS_Store" -delete

# Start Jupyter server for testing
jupyter:
	@echo "Starting Jupyter server..."
	@echo "Server URL: http://localhost:8888"
	@echo "Token: my-token"
	jupyter notebook --ip=0.0.0.0 --port=8888 --no-browser --allow-root --NotebookApp.token='my-token' 