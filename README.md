# Jupyter MCP Server

A Model Context Protocol (MCP) server integrated with Jupyter notebooks, enabling code cell execution and notebook content management through MCP tools.

## Features

- Execute code cells in Jupyter notebooks
- Add and manage markdown and code cells
- Display cell outputs including text, images, and HTML
- Collaborative editing support with jupyter-ydoc
- Automatic session and kernel management

## Project Structure

```
jupyter-mcp/
├── src/
│   ├── __init__.py          # Package initialization
│   ├── server.py            # Main entry point
│   ├── models.py            # Data models (AppConfig)
│   ├── config.py            # Configuration management
│   ├── exceptions.py        # Custom exceptions
│   ├── notebook_manager.py  # Notebook operations manager
│   ├── tools.py             # MCP tool definitions
│   └── utils.py             # Utility functions
├── tests/
│   ├── __init__.py          # Test package initialization
│   ├── conftest.py          # pytest configuration
│   ├── test_jupyter_mcp.py  # Basic functionality tests
│   └── test_deletion_sync.py # Cell deletion sync tests
├── .devcontainer/           # Development container configuration
├── .vscode/                 # VSCode settings
├── test_images/             # Test image output directory
├── test_output/             # Test output directory
├── requirements.txt         # Python dependencies
├── Dockerfile              # Docker configuration
├── Makefile                # Build and test commands
├── run_tests.sh            # Test execution script
├── env.example             # Environment variable example
├── .gitignore              # Git ignore settings
├── README.md               # This file (English)
├── README_ja.md            # Japanese README
├── CONTRIBUTING.md         # Contributing guidelines (English)
└── CONTRIBUTING_ja.md      # Contributing guidelines (Japanese)
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/jupyter-mcp.git
cd jupyter-mcp
```

2. Install dependencies:
```bash
make install
# or
pip install -r requirements.txt
```

## Configuration

The server is configured through environment variables:

- `NOTEBOOK_PATH`: Path to the notebook file (default: "notebook.ipynb")
- `SERVER_URL`: Jupyter server URL (default: "http://localhost:8888")
- `TOKEN`: Jupyter server authentication token (required)
- `KERNEL_NAME`: Specific kernel to use (optional, uses server default)
- `MCP_IMAGE_DIR`: Directory to save extracted images (default: "mcp_images")
- `TIMEOUT`: General operation timeout in seconds (default: 180)
- `STARTUP_TIMEOUT`: Startup timeout in seconds (default: 60)

### Setting Environment Variables

Copy `env.example` to `.env` and adjust as needed:

```bash
cp env.example .env
```

## Usage

### Running the Server

```bash
# Set required environment variables
export TOKEN="your-jupyter-token"
export SERVER_URL="http://localhost:8888"

# Run the server
python -m src.server
```

### Using Docker

Build and run the Docker container:

```bash
docker build -t jupyter-mcp .
docker run -e TOKEN="your-token" -p 8080:8080 jupyter-mcp
```

### Available MCP Tools

1. **add_markdown_cell**: Add a markdown cell to the notebook
2. **add_code_cell_and_execute**: Add and execute a code cell
3. **execute_cell**: Execute an existing cell by index
4. **get_all_cells**: Retrieve all cells from the notebook
5. **update_cell**: Update the content of a specific cell
6. **delete_cell**: Delete a cell by index
7. **clear_all_outputs**: Clear outputs from all code cells

## Development

### Running Tests

```bash
# Run all tests
make test

# Run specific tests
make test-basic      # Basic functionality tests
make test-deletion   # Deletion sync tests
make test-pytest     # Run tests with pytest
```

### Code Structure

- **NotebookManager**: Handles all notebook operations:
  - Loading and saving notebooks from/to Jupyter server
  - YDoc management for collaborative editing
  - Cell execution through kernel WebSocket connections
  - Kernel session management

- **MCP Tools**: Each tool is decorated with `@mcp.tool()` and handles:
  - Input validation
  - Calling appropriate NotebookManager methods
  - Formatting output for MCP responses

- **Utils**: Helper functions for:
  - Cleaning notebook data for nbformat compatibility
  - Extracting and formatting cell outputs
  - Converting between different output formats

## Error Handling

The server includes custom exception classes for better error handling:

- `ConfigurationError`: Configuration-related errors
- `NotebookError`: Notebook operation errors
- `KernelError`: Kernel execution errors
- `ServerConnectionError`: Jupyter server connection errors

## Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests for new features
5. Submit a pull request

For detailed contribution guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Testing

The project includes comprehensive tests for all functionality. Tests are organized in the `tests/` directory.

### Test Structure

```
tests/
├── __init__.py              # Test package initialization
├── conftest.py              # pytest configuration
├── test_jupyter_mcp.py      # Basic functionality tests
└── test_deletion_sync.py    # Cell deletion sync tests
```

### Running Tests

#### Using Make (Recommended)

```bash
# Install dependencies including test requirements
make install

# Run all tests
make test

# Run specific tests
make test-basic      # Basic functionality tests
make test-deletion   # Deletion sync tests
make test-pytest     # Run with pytest
```

#### Using Test Runner Script

```bash
# Run all tests
./run_tests.sh

# Run specific tests
./run_tests.sh basic      # Basic functionality tests
./run_tests.sh deletion   # Deletion sync tests
./run_tests.sh pytest     # Run with pytest
```

#### Direct Execution

```bash
# Run individual test files
python tests/test_jupyter_mcp.py
python tests/test_deletion_sync.py

# Run with pytest
pytest tests/ -v -s
```

### Test Environment

Tests require a running Jupyter server. You can start one with:

```bash
make jupyter
```

Or manually:

```bash
jupyter notebook --ip=0.0.0.0 --port=8888 --no-browser --allow-root --NotebookApp.token='my-token'
```

### Environment Variables

Copy `env.example` to `.env` and adjust as needed:

```bash
cp env.example .env
```

Default test environment variables:
- `SERVER_URL`: http://host.docker.internal:8888
- `TOKEN`: my-token
- `NOTEBOOK_PATH`: test.ipynb
- `MCP_IMAGE_DIR`: test_images

### Cleanup

Remove test outputs and cache:

```bash
make clean
```

## Language Support

- [English](README.md) (this file)
- [日本語](README_ja.md) (Japanese) 