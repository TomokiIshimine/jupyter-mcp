from typing import Any, Dict, List

import nbformat
from mcp.server.fastmcp import FastMCP

from .config import config
from .notebook_manager import NotebookManager
from .utils import convert_output_dict_to_nbformat, extract_output_from_cell

# MCP instance
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

# Global notebook manager instance
notebook_manager = NotebookManager(
    config.notebook_path, config.server_url, config.token
)


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
            output = convert_output_dict_to_nbformat(output_dict)
            if output:
                outputs.append(output)

        # Update cell outputs with nbformat Output objects
        notebook_manager.notebook.cells[cell_index].outputs = outputs

        # Extract outputs for return
        extracted_outputs = []
        for output in outputs:
            extracted = extract_output_from_cell(output)
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
            output = convert_output_dict_to_nbformat(output_dict)
            if output:
                outputs.append(output)

        # Update cell outputs with nbformat Output objects
        notebook_manager.notebook.cells[cell_index].outputs = outputs

        # Extract outputs for return
        extracted_outputs = []
        for output in outputs:
            extracted = extract_output_from_cell(output)
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
                    extracted = extract_output_from_cell(output)
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
