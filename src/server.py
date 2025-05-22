import base64
import os
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncIterator

from jupyter_kernel_client import KernelClient
from jupyter_nbmodel_client import (
    NbModelClient,
    get_jupyter_notebook_websocket_url,
)
from mcp.server.fastmcp import FastMCP, Image


@dataclass
class AppConfig:
    """Application configuration."""

    notebook_path: str = os.getenv("NOTEBOOK_PATH", "notebook.ipynb")
    server_url: str = os.getenv("SERVER_URL", "http://host.docker.internal:8888")
    token: str = os.getenv("TOKEN", "MY_TOKEN")
    mcp_image_dir: Path = Path(os.getenv("MCP_IMAGE_DIR", "mcp_images"))
    timeout: int = int(os.getenv("TIMEOUT", 180))

    def __post_init__(self):
        self.mcp_image_dir.mkdir(exist_ok=True)


config = AppConfig()

mcp = FastMCP(
    "jupyter-notebook-mcp-server",
    instructions="""
    This tool integrates Jupyter notebooks with the Model Context Protocol (MCP) system.
    It allows users to execute code cells in Jupyter notebooks and visualize the outputs,
    including text, HTML, and images. The server handles communication between the Jupyter
    kernel and the MCP client, enabling interactive data analysis and visualization through
    a consistent interface. Users can run Python code, view the results, and interact with
    generated visualizations seamlessly.
    """,
)

kernel = KernelClient(server_url=config.server_url, token=config.token)
kernel.start()


def _png_to_image_obj(b64_png: str) -> Image:
    """
    Save a base64-encoded PNG to a file and return it as a FastMCP Image object.
    """
    fname = config.mcp_image_dir / f"{uuid.uuid4().hex}.png"
    with open(fname, "wb") as f:
        f.write(base64.b64decode(b64_png))
    return Image(
        path=str(fname)
    )  # Automatically displayed by Claude Desktop and MCP Inspector


def _extract_text_from_output(output: dict) -> str:
    output_type = output.get("output_type", "")
    if output_type == "display_data" or output_type == "execute_result":
        data = output.get("data", {})

        if "image/png" in data:
            return _png_to_image_obj(data["image/png"])

        if "text/html" in data:
            return data["text/html"]

        if "text/plain" in data:
            return data["text/plain"]
    elif output_type == "stream":
        return output.get("name", "") + ": " + output.get("text", "")
    elif output_type == "error":
        return output.get("ename", "") + ": " + output.get("evalue", "")
    return ""


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
    """Add a markdown cell to the Jupyter Notebook.

    Args:
        markdown_text: Markdown text to add to the cell.

    Returns:
        A message indicating that the cell was added successfully.
    """
    async with notebook_client() as client:
        client.add_markdown_cell(markdown_text)

    return "Cell added successfully"


@mcp.tool()
async def add_code_cell_and_execute(code: str) -> list[str]:
    """Add a code cell to the Jupyter Notebook and execute it.

    Args:
        code: Code to add to the cell.

    Returns:
        A list of strings representing the output from the executed cell.
    """

    async with notebook_client() as client:
        cell_index = client.add_code_cell(code)
        execution_result = client.execute_cell(
            cell_index, kernel, timeout=config.timeout
        )
        outputs = execution_result.get("outputs", [])

        output_texts = [_extract_text_from_output(output) for output in outputs]

    return output_texts


@mcp.tool()
async def get_all_cells() -> list[str]:
    """Get all cells from the Jupyter Notebook."""
    async with notebook_client() as client:
        dict_data = client.as_dict()
        cells = dict_data.get("cells", [])

        processed_cells = []
        for cell in cells:
            processed_cell = {
                "source": cell.get("source", ""),
                "cell_type": cell.get("cell_type", ""),
                "outputs": [],
            }

            for output in cell.get("outputs", []):
                processed_cell["outputs"].append(_extract_text_from_output(output))

            processed_cells.append(processed_cell)

        return processed_cells


if __name__ == "__main__":
    mcp.run()
