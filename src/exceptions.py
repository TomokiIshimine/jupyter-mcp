"""Custom exceptions for Jupyter MCP Server."""


class JupyterMCPError(Exception):
    """Base exception for Jupyter MCP Server."""

    pass


class ConfigurationError(JupyterMCPError):
    """Raised when there's a configuration error."""

    pass


class NotebookError(JupyterMCPError):
    """Raised when there's an error with notebook operations."""

    pass


class KernelError(JupyterMCPError):
    """Raised when there's an error with kernel operations."""

    pass


class ServerConnectionError(JupyterMCPError):
    """Raised when there's an error connecting to Jupyter server."""

    pass
