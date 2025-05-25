from typing import Any, Dict, List, Optional

import nbformat
from mcp.server.fastmcp import FastMCP

from config import config
from notebook_manager import NotebookManager
from utils import convert_output_dict_to_nbformat, extract_output_from_cell

# Constants
SUCCESS_MESSAGES = {
    "markdown_added": "Markdown cell added successfully",
    "cell_updated": "Cell {index} updated successfully",
    "cell_deleted": "Cell {index} deleted successfully",
    "outputs_cleared": "All outputs cleared successfully",
    "no_output": "Cell executed successfully with no output",
}

ERROR_MESSAGES = {
    "index_out_of_range": "Error: Cell index {index} out of range",
    "not_code_cell": "Error: Can only execute code cells",
}

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


async def _validate_cell_index(cell_index: int) -> Optional[str]:
    """Validate if cell index is within range.

    Args:
        cell_index: Index to validate.

    Returns:
        Error message if invalid, None if valid.
    """
    if cell_index >= len(notebook_manager.notebook.cells):
        return ERROR_MESSAGES["index_out_of_range"].format(index=cell_index)
    return None


async def _process_execution_outputs(execution_result: Dict[str, Any]) -> List[Any]:
    """Process execution outputs and convert them to the appropriate format.

    Args:
        execution_result: Result from notebook execution.

    Returns:
        List of processed outputs.
    """
    outputs = []
    for output_dict in execution_result.get("outputs", []):
        output = convert_output_dict_to_nbformat(output_dict)
        if output:
            outputs.append(output)

    extracted_outputs = []
    for output in outputs:
        extracted = extract_output_from_cell(output)
        if extracted:
            extracted_outputs.append(extracted)

    return outputs, extracted_outputs


async def _execute_cell_common(cell_index: int) -> List[Any]:
    """Common execution logic for cells.

    Args:
        cell_index: Index of the cell to execute.

    Returns:
        List of outputs from execution.
    """
    # Validate cell index
    error_msg = await _validate_cell_index(cell_index)
    if error_msg:
        return [error_msg]

    cell = notebook_manager.notebook.cells[cell_index]
    if cell.cell_type != "code":
        return [ERROR_MESSAGES["not_code_cell"]]

    # Execute on server
    execution_result = await notebook_manager.execute_on_server(cell_index)

    # Process outputs
    outputs, extracted_outputs = await _process_execution_outputs(execution_result)

    # Update cell outputs
    notebook_manager.notebook.cells[cell_index].outputs = outputs

    # Sync and save
    await notebook_manager.sync_to_ydoc()
    await notebook_manager.save_notebook()

    return extracted_outputs if extracted_outputs else [SUCCESS_MESSAGES["no_output"]]


async def _refresh_and_sync() -> None:
    """Common pattern for refreshing from server and syncing back."""
    await notebook_manager.refresh_from_server()


async def _sync_and_save() -> None:
    """Common pattern for syncing to ydoc and saving."""
    await notebook_manager.sync_to_ydoc()
    await notebook_manager.save_notebook()


@mcp.tool()
async def add_markdown_cell(markdown_text: str) -> str:
    """Add a markdown cell to the Jupyter Notebook.

    Args:
        markdown_text: Markdown text to add to the cell.

    Returns:
        A message indicating that the cell was added successfully.
    """
    async with notebook_manager._lock:
        await _refresh_and_sync()

        # Create new markdown cell
        new_cell = nbformat.v4.new_markdown_cell(source=markdown_text)
        notebook_manager.notebook.cells.append(new_cell)

        await _sync_and_save()

    return SUCCESS_MESSAGES["markdown_added"]


@mcp.tool()
async def add_code_cell_and_execute(code: str) -> List[Any]:
    """Add a code cell to the Jupyter Notebook and execute it.

    Args:
        code: Code to add to the cell.

    Returns:
        A list of outputs from the executed cell.
    """
    async with notebook_manager._lock:
        await _refresh_and_sync()

        # Create new code cell
        new_cell = nbformat.v4.new_code_cell(source=code)
        cell_index = len(notebook_manager.notebook.cells)
        notebook_manager.notebook.cells.append(new_cell)

        # Execute the newly added cell
        return await _execute_cell_common(cell_index)


@mcp.tool()
async def execute_cell(cell_index: int) -> List[Any]:
    """Execute a specific cell in the notebook.

    Args:
        cell_index: Index of the cell to execute (0-based).

    Returns:
        A list of outputs from the executed cell.
    """
    async with notebook_manager._lock:
        await _refresh_and_sync()
        return await _execute_cell_common(cell_index)


@mcp.tool()
async def get_all_cells() -> List[Dict[str, Any]]:
    """Get all cells from the Jupyter Notebook.

    Returns:
        List of cell information dictionaries.
    """
    async with notebook_manager._lock:
        await _refresh_and_sync()

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
        await _refresh_and_sync()

        # Validate cell index
        error_msg = await _validate_cell_index(cell_index)
        if error_msg:
            return error_msg

        notebook_manager.notebook.cells[cell_index].source = new_content
        await _sync_and_save()

    return SUCCESS_MESSAGES["cell_updated"].format(index=cell_index)


@mcp.tool()
async def delete_cell(cell_index: int) -> str:
    """Delete a specific cell from the notebook.

    Args:
        cell_index: Index of the cell to delete (0-based).

    Returns:
        A message indicating success or failure.
    """
    async with notebook_manager._lock:
        await _refresh_and_sync()

        # Validate cell index
        error_msg = await _validate_cell_index(cell_index)
        if error_msg:
            return error_msg

        del notebook_manager.notebook.cells[cell_index]
        await _sync_and_save()

    return SUCCESS_MESSAGES["cell_deleted"].format(index=cell_index)


@mcp.tool()
async def clear_all_outputs() -> str:
    """Clear all outputs from all code cells in the notebook.

    Returns:
        A message indicating success.
    """
    async with notebook_manager._lock:
        await _refresh_and_sync()

        for cell in notebook_manager.notebook.cells:
            if cell.cell_type == "code":
                cell.outputs = []

        await _sync_and_save()

    return SUCCESS_MESSAGES["outputs_cleared"]
