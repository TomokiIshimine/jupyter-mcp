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
async def add_code_cell_and_execute(code: str) -> str:
    """Add a code cell to the jupyter notebook and execute it.

    Args:
        code: Code to add to the cell.

    Returns:
        A message indicating that the cell was added successfully.
    """

    async with notebook_client() as client:
        cell_index = client.add_code_cell(code)
        execution_result = client.execute_cell(cell_index, kernel)
        outputs = execution_result.get("outputs", [])

        output_texts = []
        for output in outputs:
            output_type = output.get("output_type", "")
            if output_type == "display_data":
                data = output.get("data", {})
                if "text/plain" in data:
                    output_texts.append(data["text/plain"])

    return "\n".join(output_texts)


if __name__ == "__main__":
    mcp.run()
