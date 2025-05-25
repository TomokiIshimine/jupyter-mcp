import base64
import uuid
from pathlib import Path
from typing import Any, Dict

import nbformat
from mcp.server.fastmcp import Image

from config import config


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


def png_to_image_obj(b64_png: str) -> Image:
    """
    Save a base64-encoded PNG to a file and return it as a FastMCP Image object.
    """
    fname = config.mcp_image_dir / f"{uuid.uuid4().hex}.png"
    with open(fname, "wb") as f:
        f.write(base64.b64decode(b64_png))
    return Image(path=str(fname))


def extract_output_from_cell(output: Any) -> Any:
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
            return png_to_image_obj(data["image/png"])

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


def convert_output_dict_to_nbformat(
    output_dict: Dict[str, Any],
) -> nbformat.NotebookNode:
    """Convert output dictionary to nbformat Output object."""
    if output_dict["output_type"] == "stream":
        return nbformat.v4.new_output(
            output_type="stream",
            name=output_dict["name"],
            text=output_dict["text"],
        )
    elif output_dict["output_type"] == "display_data":
        return nbformat.v4.new_output(
            output_type="display_data",
            data=output_dict["data"],
            metadata=output_dict.get("metadata", {}),
        )
    elif output_dict["output_type"] == "execute_result":
        return nbformat.v4.new_output(
            output_type="execute_result",
            execution_count=output_dict["execution_count"],
            data=output_dict["data"],
            metadata=output_dict.get("metadata", {}),
        )
    elif output_dict["output_type"] == "error":
        return nbformat.v4.new_output(
            output_type="error",
            ename=output_dict["ename"],
            evalue=output_dict["evalue"],
            traceback=output_dict["traceback"],
        )
    else:
        return None
