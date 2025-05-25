import asyncio
import base64
import json
import os
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, urlunparse

import nbformat
import websockets
from jupyter_ydoc import YNotebook
from mcp.server.fastmcp import FastMCP, Image


@dataclass
class AppConfig:
    """Application configuration."""

    notebook_path: str = os.getenv("NOTEBOOK_PATH", "notebook.ipynb")
    server_url: str = os.getenv("SERVER_URL", "http://localhost:8888")
    token: str = os.getenv("TOKEN", "")
    kernel_name: str = os.getenv("KERNEL_NAME", "python3")
    mcp_image_dir: Path = Path(os.getenv("MCP_IMAGE_DIR", "mcp_images"))
    timeout: int = int(os.getenv("TIMEOUT", 180))
    startup_timeout: int = int(os.getenv("STARTUP_TIMEOUT", 60))

    def __post_init__(self):
        self.mcp_image_dir.mkdir(exist_ok=True)
        if not self.token:
            raise ValueError(
                "TOKEN environment variable must be set to connect to Jupyter Server"
            )


config = AppConfig()

mcp = FastMCP(
    "jupyter-notebook-mcp-server",
    instructions="""
    This tool integrates Jupyter notebooks with the Model Context Protocol (MCP) system.
    It allows users to execute code cells in Jupyter notebooks and visualize the outputs,
    including text, HTML, and images. The server uses jupyter-ydoc for collaborative editing
    and nbformat for notebook structure handling.
    Users can run Python code, view the results, and interact with generated visualizations seamlessly.
    """,
)


def clean_notebook_for_nbformat(notebook_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Remove properties that nbformat doesn't recognize."""
    # Create a deep copy to avoid modifying the original
    import copy

    cleaned = copy.deepcopy(notebook_dict)

    # Remove transient from outputs if present
    if "cells" in cleaned:
        for cell in cleaned["cells"]:
            if "outputs" in cell:
                for output in cell["outputs"]:
                    if "transient" in output:
                        del output["transient"]

    return cleaned


class NotebookManager:
    """Manages notebook operations using YDoc and nbformat."""

    def __init__(self, notebook_path: str, server_url: str, token: str):
        self.notebook_path = notebook_path
        self.server_url = server_url
        self.token = token
        self.ydoc: Optional[YNotebook] = None
        self._lock = asyncio.Lock()
        self.ws_connection = None

    def _get_websocket_url(self) -> str:
        """Convert HTTP URL to WebSocket URL for YDoc connection."""
        parsed = urlparse(self.server_url)
        ws_scheme = "wss" if parsed.scheme == "https" else "ws"
        ws_url = urlunparse(
            (
                ws_scheme,
                parsed.netloc,
                f"/api/collaboration/room/json:notebook:{self.notebook_path}",
                "",
                f"token={self.token}",
                "",
            )
        )
        return ws_url

    async def initialize(self):
        """Initialize the notebook manager."""
        async with self._lock:
            # First, check if notebook exists on server
            import aiohttp

            async with aiohttp.ClientSession() as session:
                # Get notebook content from server
                notebook_url = f"{self.server_url}/api/contents/{self.notebook_path}"
                headers = {"Authorization": f"token {self.token}"}

                async with session.get(notebook_url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        notebook_content = data.get("content", {})
                        # Clean the notebook content before using nbformat
                        cleaned_content = clean_notebook_for_nbformat(notebook_content)
                        self.notebook = nbformat.from_dict(cleaned_content)
                    elif resp.status == 404:
                        # Create new notebook
                        self.notebook = nbformat.v4.new_notebook()
                        await self.save_notebook_to_server()
                    else:
                        raise Exception(f"Failed to access notebook: {resp.status}")

            # Initialize YDoc for collaborative editing
            self.ydoc = YNotebook()
            # YDoc expects a notebook dict
            self.ydoc.set(self.notebook)

    async def save_notebook_to_server(self):
        """Save the notebook to Jupyter server."""
        import aiohttp

        async with aiohttp.ClientSession() as session:
            notebook_url = f"{self.server_url}/api/contents/{self.notebook_path}"
            headers = {"Authorization": f"token {self.token}"}

            # NotebookNode is dict-like, so we can use it directly
            data = {
                "type": "notebook",
                "format": "json",
                "content": self.notebook,
            }

            async with session.put(notebook_url, headers=headers, json=data) as resp:
                if resp.status not in [200, 201]:
                    raise Exception(f"Failed to save notebook: {resp.status}")

    async def save_notebook(self):
        """Save the notebook to server."""
        # サーバーへの保存のみ実行（ローカル保存は削除）
        await self.save_notebook_to_server()

    async def sync_from_ydoc(self):
        """Sync notebook from YDoc."""
        if self.ydoc:
            # Get the notebook dict from YDoc
            notebook_dict = self.ydoc.get()
            if notebook_dict:
                self.notebook = nbformat.from_dict(notebook_dict)

    async def sync_to_ydoc(self):
        """Sync notebook to YDoc."""
        if self.ydoc:
            # YDoc expects a notebook dict
            self.ydoc.set(self.notebook)

    async def refresh_from_server(self):
        """Refresh notebook content from Jupyter server."""
        import aiohttp

        async with aiohttp.ClientSession() as session:
            notebook_url = f"{self.server_url}/api/contents/{self.notebook_path}"
            headers = {"Authorization": f"token {self.token}"}

            async with session.get(notebook_url, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    notebook_content = data.get("content", {})
                    # Clean the notebook content before using nbformat
                    cleaned_content = clean_notebook_for_nbformat(notebook_content)
                    self.notebook = nbformat.from_dict(cleaned_content)
                    # Update YDoc with the latest content
                    if self.ydoc:
                        self.ydoc.set(self.notebook)
                else:
                    raise Exception(f"Failed to refresh notebook: {resp.status}")

    async def execute_on_server(self, cell_index: int) -> Dict[str, Any]:
        """Execute a cell on the Jupyter server."""
        import aiohttp

        async with aiohttp.ClientSession() as session:
            # Create a session and kernel
            sessions_url = f"{self.server_url}/api/sessions"
            headers = {"Authorization": f"token {self.token}"}

            # Check for existing session
            async with session.get(sessions_url, headers=headers) as resp:
                sessions = await resp.json()
                session_id = None
                for s in sessions:
                    if s.get("notebook", {}).get("path") == self.notebook_path:
                        session_id = s["id"]
                        kernel_id = s["kernel"]["id"]
                        break

            # Create new session if needed
            if not session_id:
                data = {
                    "path": self.notebook_path,
                    "type": "notebook",
                    "kernel": {"name": config.kernel_name},
                }
                async with session.post(
                    sessions_url, headers=headers, json=data
                ) as resp:
                    session_data = await resp.json()
                    session_id = session_data["id"]
                    kernel_id = session_data["kernel"]["id"]

            # Execute code via kernel
            kernel_url = f"{self.server_url}/api/kernels/{kernel_id}"
            ws_url = f"{kernel_url.replace('http', 'ws')}/channels?token={self.token}"

            # Connect to kernel websocket
            async with websockets.connect(ws_url) as ws:
                # Send execute request
                code = self.notebook.cells[cell_index].source
                msg_id = str(uuid.uuid4())

                execute_request = {
                    "header": {
                        "msg_id": msg_id,
                        "msg_type": "execute_request",
                        "session": session_id,
                    },
                    "parent_header": {},
                    "metadata": {},
                    "content": {
                        "code": code,
                        "silent": False,
                        "store_history": True,
                        "user_expressions": {},
                        "allow_stdin": False,
                    },
                }

                await ws.send(json.dumps(execute_request))

                # Collect outputs
                outputs = []
                while True:
                    msg = json.loads(await ws.recv())
                    msg_type = msg["header"]["msg_type"]

                    if msg["parent_header"].get("msg_id") != msg_id:
                        continue

                    if msg_type == "stream":
                        outputs.append(
                            {
                                "output_type": "stream",
                                "name": msg["content"]["name"],
                                "text": msg["content"]["text"],
                            }
                        )
                    elif msg_type == "display_data":
                        outputs.append(
                            {
                                "output_type": "display_data",
                                "data": msg["content"]["data"],
                                "metadata": msg["content"]["metadata"],
                            }
                        )
                    elif msg_type == "execute_result":
                        outputs.append(
                            {
                                "output_type": "execute_result",
                                "execution_count": msg["content"]["execution_count"],
                                "data": msg["content"]["data"],
                                "metadata": msg["content"]["metadata"],
                            }
                        )
                    elif msg_type == "error":
                        outputs.append(
                            {
                                "output_type": "error",
                                "ename": msg["content"]["ename"],
                                "evalue": msg["content"]["evalue"],
                                "traceback": msg["content"]["traceback"],
                            }
                        )
                    elif msg_type == "execute_reply":
                        break

                return {"outputs": outputs}


# Global notebook manager instance
notebook_manager = NotebookManager(
    config.notebook_path, config.server_url, config.token
)


def _png_to_image_obj(b64_png: str) -> Image:
    """
    Save a base64-encoded PNG to a file and return it as a FastMCP Image object.
    """
    fname = config.mcp_image_dir / f"{uuid.uuid4().hex}.png"
    with open(fname, "wb") as f:
        f.write(base64.b64decode(b64_png))
    return Image(path=str(fname))


def _extract_output_from_cell(output: Any) -> Any:
    """Extract readable output from a cell output."""
    # Handle both dict and NotebookNode objects
    if hasattr(output, "output_type"):
        output_type = output.output_type
    else:
        output_type = output.get("output_type", "")

    if output_type in ["display_data", "execute_result"]:
        # Get data attribute or dict key
        if hasattr(output, "data"):
            data = output.data
        else:
            data = output.get("data", {})

        if "image/png" in data:
            return _png_to_image_obj(data["image/png"])

        if "text/html" in data:
            return data["text/html"]

        if "text/plain" in data:
            return data["text/plain"]

    elif output_type == "stream":
        if hasattr(output, "text"):
            return output.text
        else:
            return output.get("text", "")

    elif output_type == "error":
        if hasattr(output, "ename"):
            ename = output.ename
            evalue = output.evalue
            traceback = output.traceback
        else:
            ename = output.get("ename", "Error")
            evalue = output.get("evalue", "")
            traceback = output.get("traceback", [])

        return f"{ename}: {evalue}\n" + "\n".join(traceback)

    return ""


@mcp.tool()
async def add_markdown_cell(markdown_text: str) -> str:
    """Add a markdown cell to the Jupyter Notebook.

    Args:
        markdown_text: Markdown text to add to the cell.

    Returns:
        A message indicating that the cell was added successfully.
    """
    async with notebook_manager._lock:
        await notebook_manager.refresh_from_server()

        # Create new markdown cell
        new_cell = nbformat.v4.new_markdown_cell(source=markdown_text)
        notebook_manager.notebook.cells.append(new_cell)

        await notebook_manager.sync_to_ydoc()
        await notebook_manager.save_notebook()

    return "Markdown cell added successfully"


@mcp.tool()
async def add_code_cell_and_execute(code: str) -> List[Any]:
    """Add a code cell to the Jupyter Notebook and execute it.

    Args:
        code: Code to add to the cell.

    Returns:
        A list of outputs from the executed cell.
    """
    async with notebook_manager._lock:
        await notebook_manager.refresh_from_server()

        # Create new code cell
        new_cell = nbformat.v4.new_code_cell(source=code)
        cell_index = len(notebook_manager.notebook.cells)
        notebook_manager.notebook.cells.append(new_cell)

        # Execute on server
        execution_result = await notebook_manager.execute_on_server(cell_index)

        # Convert dict outputs to nbformat Output objects
        outputs = []
        for output_dict in execution_result.get("outputs", []):
            if output_dict["output_type"] == "stream":
                output = nbformat.v4.new_output(
                    output_type="stream",
                    name=output_dict["name"],
                    text=output_dict["text"],
                )
            elif output_dict["output_type"] == "display_data":
                output = nbformat.v4.new_output(
                    output_type="display_data",
                    data=output_dict["data"],
                    metadata=output_dict.get("metadata", {}),
                )
            elif output_dict["output_type"] == "execute_result":
                output = nbformat.v4.new_output(
                    output_type="execute_result",
                    execution_count=output_dict["execution_count"],
                    data=output_dict["data"],
                    metadata=output_dict.get("metadata", {}),
                )
            elif output_dict["output_type"] == "error":
                output = nbformat.v4.new_output(
                    output_type="error",
                    ename=output_dict["ename"],
                    evalue=output_dict["evalue"],
                    traceback=output_dict["traceback"],
                )
            else:
                continue
            outputs.append(output)

        # Update cell outputs with nbformat Output objects
        notebook_manager.notebook.cells[cell_index].outputs = outputs

        # Extract outputs for return
        extracted_outputs = []
        for output in outputs:
            extracted = _extract_output_from_cell(output)
            if extracted:
                extracted_outputs.append(extracted)

        await notebook_manager.sync_to_ydoc()
        await notebook_manager.save_notebook()

    return (
        extracted_outputs
        if extracted_outputs
        else ["Cell executed successfully with no output"]
    )


@mcp.tool()
async def execute_cell(cell_index: int) -> List[Any]:
    """Execute a specific cell in the notebook.

    Args:
        cell_index: Index of the cell to execute (0-based).

    Returns:
        A list of outputs from the executed cell.
    """
    async with notebook_manager._lock:
        await notebook_manager.refresh_from_server()

        if cell_index >= len(notebook_manager.notebook.cells):
            return [f"Error: Cell index {cell_index} out of range"]

        cell = notebook_manager.notebook.cells[cell_index]
        if cell.cell_type != "code":
            return ["Error: Can only execute code cells"]

        # Execute on server
        execution_result = await notebook_manager.execute_on_server(cell_index)

        # Convert dict outputs to nbformat Output objects
        outputs = []
        for output_dict in execution_result.get("outputs", []):
            if output_dict["output_type"] == "stream":
                output = nbformat.v4.new_output(
                    output_type="stream",
                    name=output_dict["name"],
                    text=output_dict["text"],
                )
            elif output_dict["output_type"] == "display_data":
                output = nbformat.v4.new_output(
                    output_type="display_data",
                    data=output_dict["data"],
                    metadata=output_dict.get("metadata", {}),
                )
            elif output_dict["output_type"] == "execute_result":
                output = nbformat.v4.new_output(
                    output_type="execute_result",
                    execution_count=output_dict["execution_count"],
                    data=output_dict["data"],
                    metadata=output_dict.get("metadata", {}),
                )
            elif output_dict["output_type"] == "error":
                output = nbformat.v4.new_output(
                    output_type="error",
                    ename=output_dict["ename"],
                    evalue=output_dict["evalue"],
                    traceback=output_dict["traceback"],
                )
            else:
                continue
            outputs.append(output)

        # Update cell outputs with nbformat Output objects
        notebook_manager.notebook.cells[cell_index].outputs = outputs

        # Extract outputs for return
        extracted_outputs = []
        for output in outputs:
            extracted = _extract_output_from_cell(output)
            if extracted:
                extracted_outputs.append(extracted)

        await notebook_manager.sync_to_ydoc()
        await notebook_manager.save_notebook()

    return (
        extracted_outputs
        if extracted_outputs
        else ["Cell executed successfully with no output"]
    )


@mcp.tool()
async def get_all_cells() -> List[Dict[str, Any]]:
    """Get all cells from the Jupyter Notebook."""
    async with notebook_manager._lock:
        await notebook_manager.refresh_from_server()

        cells = []
        for idx, cell in enumerate(notebook_manager.notebook.cells):
            cell_info = {
                "index": idx,
                "cell_type": cell.cell_type,
                "source": cell.source,
                "outputs": [],
            }

            if cell.cell_type == "code" and hasattr(cell, "outputs"):
                for output in cell.outputs:
                    extracted = _extract_output_from_cell(output)
                    if extracted:
                        cell_info["outputs"].append(extracted)

            cells.append(cell_info)

    return cells


@mcp.tool()
async def update_cell(cell_index: int, new_content: str) -> str:
    """Update the content of a specific cell.

    Args:
        cell_index: Index of the cell to update (0-based).
        new_content: New content for the cell.

    Returns:
        A message indicating success or failure.
    """
    async with notebook_manager._lock:
        await notebook_manager.refresh_from_server()

        if cell_index >= len(notebook_manager.notebook.cells):
            return f"Error: Cell index {cell_index} out of range"

        notebook_manager.notebook.cells[cell_index].source = new_content

        await notebook_manager.sync_to_ydoc()
        await notebook_manager.save_notebook()

    return f"Cell {cell_index} updated successfully"


@mcp.tool()
async def delete_cell(cell_index: int) -> str:
    """Delete a specific cell from the notebook.

    Args:
        cell_index: Index of the cell to delete (0-based).

    Returns:
        A message indicating success or failure.
    """
    async with notebook_manager._lock:
        await notebook_manager.refresh_from_server()

        if cell_index >= len(notebook_manager.notebook.cells):
            return f"Error: Cell index {cell_index} out of range"

        del notebook_manager.notebook.cells[cell_index]

        await notebook_manager.sync_to_ydoc()
        await notebook_manager.save_notebook()

    return f"Cell {cell_index} deleted successfully"


@mcp.tool()
async def clear_all_outputs() -> str:
    """Clear all outputs from all code cells in the notebook."""
    async with notebook_manager._lock:
        await notebook_manager.refresh_from_server()

        for cell in notebook_manager.notebook.cells:
            if cell.cell_type == "code":
                cell.outputs = []

        await notebook_manager.sync_to_ydoc()
        await notebook_manager.save_notebook()

    return "All outputs cleared successfully"


async def startup():
    """Initialize the notebook manager on startup."""
    await notebook_manager.initialize()


if __name__ == "__main__":
    # Run startup before starting the MCP server
    asyncio.run(startup())
    mcp.run()
