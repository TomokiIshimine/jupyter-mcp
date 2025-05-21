import os
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncIterator

from jupyter_kernel_client import KernelClient
from jupyter_nbmodel_client import (
    NbModelClient,
    get_jupyter_notebook_websocket_url,
)
from mcp.server.fastmcp import FastMCP


@dataclass
class AppConfig:
    """Application configuration."""

    notebook_path: str = os.getenv("NOTEBOOK_PATH", "notebook.ipynb")
    server_url: str = os.getenv("SERVER_URL", "http://localhost:8888")
    token: str = os.getenv("TOKEN", "MY_TOKEN")
    mcp_image_dir: Path = Path(os.getenv("MCP_IMAGE_DIR", "mcp_images"))

    def __post_init__(self):
        self.mcp_image_dir.mkdir(exist_ok=True)


config = AppConfig()

mcp = FastMCP("jupyter-mcp-server")

kernel = KernelClient(server_url=config.server_url, token=config.token)
kernel.start()


@asynccontextmanager
async def notebook_client() -> AsyncIterator[NbModelClient]:
    """Provides an initialized NbModelClient as an asynchronous context manager."""
    client = NbModelClient(
        get_jupyter_notebook_websocket_url(
            server_url=config.server_url, token=config.token, path=config.notebook_path
        )
    )
    await client.start()
    try:
        yield client
    finally:
        await client.stop()


@mcp.tool()
async def add_markdown_cell(markdown_text: str) -> str:
    """Add a markdown cell to the jupyter notebook.

    Args:
        markdown_text: Markdown text to add to the cell.

    Returns:
        A message indicating that the cell was added successfully.
    """
    async with notebook_client() as client:
        client.add_markdown_cell(markdown_text)

    return "Cell added successfully"


@mcp.tool()
async def test(text: str) -> str:
    return f"Hello, {text}!"


if __name__ == "__main__":
    mcp.run()
