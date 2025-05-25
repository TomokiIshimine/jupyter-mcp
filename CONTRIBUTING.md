# Contributing Guidelines

Thank you for considering contributing to the Jupyter MCP Server project!

## Development Environment Setup

1. Fork the repository
2. Clone locally:
   ```bash
   git clone https://github.com/yourusername/jupyter-mcp.git
   cd jupyter-mcp
   ```

3. Install dependencies:
   ```bash
   make install
   ```

4. Set up environment variables:
   ```bash
   cp env.example .env
   # Edit the .env file to set appropriate values
   ```

## Development Workflow

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Implement your changes

3. Run tests:
   ```bash
   make test
   ```

4. Check code style:
   ```bash
   # Run formatter if needed
   black src/ tests/
   ```

5. Commit and push:
   ```bash
   git add .
   git commit -m "feat: description of new feature"
   git push origin feature/your-feature-name
   ```

6. Create a pull request

## Coding Standards

- Follow Python PEP 8
- Use type hints
- Write proper docstrings
- Maintain test coverage

## Testing

When adding new features, please add corresponding tests:

- Unit tests: Add to `tests/` directory
- Integration tests: Add to existing test files

Running tests:
```bash
# All tests
make test

# Specific tests
make test-basic
make test-deletion
```

## Bug Reports

If you find a bug, please create an Issue with the following information:

- Detailed description of the problem
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment information (OS, Python version, etc.)

## Feature Requests

New feature proposals are welcome. Please explain the following in an Issue:

- Feature details
- Use cases
- Implementation suggestions (if any)

## Commit Messages

We recommend using Conventional Commits format:

- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation updates
- `test:` Test additions/modifications
- `refactor:` Refactoring

## Questions

If you have questions, please create an Issue or contact the project maintainers directly.

Thank you for your cooperation! 