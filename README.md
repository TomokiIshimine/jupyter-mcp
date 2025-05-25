# Jupyter MCP Server

A Model Context Protocol (MCP) server that integrates with Jupyter notebooks, allowing execution of code cells and management of notebook content through MCP tools.

## Features

- Execute code cells in Jupyter notebooks
- Add and manage markdown and code cells
- View cell outputs including text, images, and HTML
- Collaborative editing support via jupyter-ydoc
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
│   └── ...                  # Test files
├── requirements.txt         # Python dependencies
├── Dockerfile              # Docker configuration
└── README.md               # This file
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/jupyter-mcp.git
cd jupyter-mcp
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

The server is configured through environment variables:

- `NOTEBOOK_PATH`: Path to the notebook file (default: "notebook.ipynb")
- `SERVER_URL`: Jupyter server URL (default: "http://localhost:8888")
- `TOKEN`: Jupyter server authentication token (required)
- `KERNEL_NAME`: Specific kernel to use (optional, defaults to server's default)
- `MCP_IMAGE_DIR`: Directory to store extracted images (default: "mcp_images")
- `TIMEOUT`: General operation timeout in seconds (default: 180)
- `STARTUP_TIMEOUT`: Startup timeout in seconds (default: 60)

## Usage

### Running the Server

```bash
# Set required environment variables
export TOKEN="your-jupyter-token"
export SERVER_URL="http://localhost:8888"

# Run the server
python -m src.server
```

### Using with Docker

Build and run the Docker container:

```bash
docker build -t jupyter-mcp .
docker run -e TOKEN="your-token" -p 8080:8080 jupyter-mcp
```

### Available MCP Tools

1. **add_markdown_cell**: Add a markdown cell to the notebook
2. **add_code_cell_and_execute**: Add a code cell and execute it
3. **execute_cell**: Execute an existing cell by index
4. **get_all_cells**: Retrieve all cells from the notebook
5. **update_cell**: Update the content of a specific cell
6. **delete_cell**: Delete a cell by index
7. **clear_all_outputs**: Clear all outputs from code cells

## Development

### Running Tests

```bash
pytest
```

### Code Structure

- **NotebookManager**: Handles all notebook operations including:
  - Loading and saving notebooks from/to Jupyter server
  - Managing YDoc for collaborative editing
  - Executing cells via kernel WebSocket connections
  - Managing kernel sessions

- **MCP Tools**: Each tool is decorated with `@mcp.tool()` and handles:
  - Input validation
  - Calling appropriate NotebookManager methods
  - Formatting outputs for MCP responses

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
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

[Your License Here]

## Testing

The project includes comprehensive tests for all functionality. Tests are organized in the `tests/` directory.

### Test Structure

```
tests/
├── __init__.py
├── conftest.py              # pytest configuration
├── test_jupyter_mcp.py      # Basic functionality tests
└── test_deletion_sync.py    # Cell deletion synchronization tests
```

### Running Tests

#### Using Make (Recommended)

```bash
# Install dependencies including test requirements
make install

# Run all tests
make test

# Run specific tests
make test-basic      # Run basic functionality test
make test-deletion   # Run deletion sync test
make test-pytest     # Run tests with pytest
```

#### Using the test runner script

```bash
# Run all tests
./run_tests.sh

# Run specific tests
./run_tests.sh basic      # Basic functionality test
./run_tests.sh deletion   # Deletion sync test
./run_tests.sh pytest     # Run with pytest
```

#### Direct execution

```bash
# Run individual test files
python tests/test_jupyter_mcp.py
python tests/test_deletion_sync.py

# Run with pytest
pytest tests/ -v -s
```

### Test Environment

Tests require a running Jupyter server. You can start one using:

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

### Cleaning Up

Remove test outputs and cache:

```bash
make clean
``` 