import base64
import copy
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, Union

import nbformat
from mcp.server.fastmcp import Image

from config import config


def clean_notebook_for_nbformat(notebook_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Remove properties that nbformat doesn't recognize.

    Args:
        notebook_dict: The notebook dictionary to clean

    Returns:
        A cleaned copy of the notebook dictionary
    """
    cleaned = copy.deepcopy(notebook_dict)

    if "cells" not in cleaned:
        return cleaned

    for cell in cleaned["cells"]:
        if "outputs" not in cell:
            continue

        for output in cell["outputs"]:
            if "transient" in output:
                del output["transient"]

    return cleaned


def png_to_image_obj(b64_png: str) -> Image:
    """Save a base64-encoded PNG to a file and return it as a FastMCP Image object.

    Args:
        b64_png: Base64-encoded PNG data

    Returns:
        FastMCP Image object

    Raises:
        ValueError: If the base64 data is invalid
    """
    try:
        png_data = base64.b64decode(b64_png)
    except Exception as e:
        raise ValueError(f"Invalid base64 PNG data: {e}")

    fname = config.mcp_image_dir / f"{uuid.uuid4().hex}.png"

    try:
        with open(fname, "wb") as f:
            f.write(png_data)
    except Exception as e:
        raise IOError(f"Failed to write image file {fname}: {e}")

    return Image(path=str(fname))


def _get_attribute_or_key(obj: Any, key: str, default: Any = None) -> Any:
    """Get attribute if it exists, otherwise get from dict with default.

    Args:
        obj: Object to get value from
        key: Attribute/key name
        default: Default value if not found

    Returns:
        The value found or default
    """
    if hasattr(obj, key):
        return getattr(obj, key)
    return obj.get(key, default) if hasattr(obj, "get") else default


def _extract_display_data(data: Dict[str, Any]) -> Any:
    """Extract display data in priority order.

    Args:
        data: Data dictionary from output

    Returns:
        Extracted data or empty string
    """
    if "image/png" in data:
        return png_to_image_obj(data["image/png"])
    if "text/html" in data:
        return data["text/html"]
    if "text/plain" in data:
        return data["text/plain"]
    return ""


def _extract_error_output(output: Any) -> str:
    """Extract error information from output.

    Args:
        output: Error output object

    Returns:
        Formatted error string
    """
    ename = _get_attribute_or_key(output, "ename", "Error")
    evalue = _get_attribute_or_key(output, "evalue", "")
    traceback = _get_attribute_or_key(output, "traceback", [])

    return f"{ename}: {evalue}\n" + "\n".join(traceback)


def extract_output_from_cell(output: Any) -> Any:
    """Extract readable output from a cell output.

    Args:
        output: Cell output object (dict or NotebookNode)

    Returns:
        Extracted output data or empty string
    """
    output_type = _get_attribute_or_key(output, "output_type", "")

    if output_type in ["display_data", "execute_result"]:
        data = _get_attribute_or_key(output, "data", {})
        return _extract_display_data(data)

    elif output_type == "stream":
        return _get_attribute_or_key(output, "text", "")

    elif output_type == "error":
        return _extract_error_output(output)

    return ""


def convert_output_dict_to_nbformat(
    output_dict: Dict[str, Any],
) -> Optional[nbformat.NotebookNode]:
    """Convert output dictionary to nbformat Output object.

    Args:
        output_dict: Dictionary containing output data

    Returns:
        nbformat NotebookNode or None if output type is unsupported
    """
    output_type = output_dict.get("output_type")

    if output_type == "stream":
        return nbformat.v4.new_output(
            output_type="stream",
            name=output_dict["name"],
            text=output_dict["text"],
        )

    elif output_type == "display_data":
        return nbformat.v4.new_output(
            output_type="display_data",
            data=output_dict["data"],
            metadata=output_dict.get("metadata", {}),
        )

    elif output_type == "execute_result":
        return nbformat.v4.new_output(
            output_type="execute_result",
            execution_count=output_dict["execution_count"],
            data=output_dict["data"],
            metadata=output_dict.get("metadata", {}),
        )

    elif output_type == "error":
        return nbformat.v4.new_output(
            output_type="error",
            ename=output_dict["ename"],
            evalue=output_dict["evalue"],
            traceback=output_dict["traceback"],
        )

    return None
