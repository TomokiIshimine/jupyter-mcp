"""Pytest configuration for Jupyter MCP tests"""

import os
import sys
from pathlib import Path

# Try to load .env file if it exists
try:
    from dotenv import load_dotenv

    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✓ Loaded environment variables from {env_path}")
except ImportError:
    print("⚠ python-dotenv not installed, skipping .env file loading")

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Default test environment variables
TEST_ENV = {
    "SERVER_URL": "http://host.docker.internal:8888",
    "TOKEN": "my-token",
    "NOTEBOOK_PATH": "test.ipynb",
    "MCP_IMAGE_DIR": "test_images",
}

# Set environment variables if not already set
for key, value in TEST_ENV.items():
    if key not in os.environ:
        os.environ[key] = value
