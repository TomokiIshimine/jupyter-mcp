#!/bin/bash
# Jupyter MCP Server Test Runner

set -e

echo "=== Jupyter MCP Server Test Runner ==="
echo

# Load .env file if it exists
if [ -f .env ]; then
    echo "Loading environment variables from .env file..."
    export $(cat .env | grep -v '^#' | xargs)
    echo "✓ Environment variables loaded"
    echo
fi

# Check if Jupyter server is running
echo "Checking Jupyter server connection..."
if ! curl -s -H "Authorization: token ${TOKEN:-my-token}" "${SERVER_URL:-http://host.docker.internal:8888}/api" > /dev/null; then
    echo "❌ Error: Cannot connect to Jupyter server at ${SERVER_URL:-http://host.docker.internal:8888}"
    echo "Please ensure Jupyter server is running with the correct token."
    exit 1
fi
echo "✓ Jupyter server is accessible"
echo

# Create test output directory
mkdir -p test_output
mkdir -p test_images

# Run tests based on argument
if [ "$1" = "pytest" ]; then
    echo "Running tests with pytest..."
    pytest tests/ -v -s
elif [ "$1" = "basic" ]; then
    echo "Running basic test..."
    python tests/test_jupyter_mcp.py
elif [ "$1" = "deletion" ]; then
    echo "Running deletion sync test..."
    python tests/test_deletion_sync.py
else
    echo "Running all tests..."
    echo
    echo "1. Basic functionality test:"
    python tests/test_jupyter_mcp.py
    echo
    echo "2. Deletion synchronization test:"
    python tests/test_deletion_sync.py
fi

echo
echo "=== Test run completed ===" 