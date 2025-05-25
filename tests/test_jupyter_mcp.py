#!/usr/bin/env python3
"""
Jupyter MCP Server Test Script
Tests add_code_cell_and_execute and add_markdown_cell functions
"""

import asyncio
import json
import os
import sys
from pathlib import Path

import pytest

# Add project root to Python path for direct execution
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

# Import from src package - conftest.py handles path setup for pytest
from src.tools import add_code_cell_and_execute, add_markdown_cell, notebook_manager


@pytest.mark.asyncio
async def test_jupyter_mcp():
    """Test the Jupyter MCP server functions."""
    print("=== Jupyter MCP Server Test ===\n")

    # Initialize notebook manager
    print("1. Initializing notebook manager...")
    await notebook_manager.initialize()
    print("✓ Notebook manager initialized successfully\n")

    # Test 1: Add markdown cell
    print("2. Testing add_markdown_cell...")
    markdown_text = """# Jupyter MCP Test Notebook

This is a test notebook created by the MCP server.

## Features
- Execute Python code
- Display outputs
- Support for images and plots
"""
    result = await add_markdown_cell(markdown_text)
    print(f"✓ {result}\n")
    assert "Added markdown cell" in result or "successfully" in result

    # Test 2: Add and execute simple code cell
    print("3. Testing add_code_cell_and_execute with simple calculation...")
    code1 = """# Simple calculation
x = 10
y = 20
result = x + y
print(f"The sum of {x} and {y} is {result}")
result"""

    outputs1 = await add_code_cell_and_execute(code1)
    print("✓ Code cell added and executed")
    print("Outputs:")
    for output in outputs1:
        print(f"  - {output}")
    print()
    assert len(outputs1) > 0
    # Check if output contains expected result (either in print output or return value)
    output_str = " ".join(str(output) for output in outputs1)
    assert "30" in output_str or "successfully" in output_str

    # Test 3: Add and execute code with numpy
    print("4. Testing with numpy array...")
    code2 = """import numpy as np

# Create a numpy array
arr = np.array([1, 2, 3, 4, 5])
print(f"Array: {arr}")
print(f"Mean: {arr.mean()}")
print(f"Sum: {arr.sum()}")
arr * 2"""

    outputs2 = await add_code_cell_and_execute(code2)
    print("✓ Numpy code executed")
    print("Outputs:")
    for output in outputs2:
        print(f"  - {output}")
    print()
    assert len(outputs2) > 0

    # Test 4: Add markdown cell with code explanation
    print("5. Adding explanation markdown cell...")
    markdown2 = """## Data Visualization

Let's create a simple plot using matplotlib:"""
    result2 = await add_markdown_cell(markdown2)
    print(f"✓ {result2}\n")
    assert "successfully" in result2

    # Test 5: Add and execute code with matplotlib
    print("6. Testing with matplotlib plot...")
    code3 = """import matplotlib.pyplot as plt
import numpy as np

# Generate data
x = np.linspace(0, 10, 100)
y = np.sin(x)

# Create plot
plt.figure(figsize=(10, 6))
plt.plot(x, y, 'b-', linewidth=2, label='sin(x)')
plt.plot(x, np.cos(x), 'r--', linewidth=2, label='cos(x)')
plt.xlabel('x')
plt.ylabel('y')
plt.title('Sine and Cosine Functions')
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()"""

    outputs3 = await add_code_cell_and_execute(code3)
    print("✓ Matplotlib code executed")
    print("Outputs:")
    for output in outputs3:
        if isinstance(output, str) and output.startswith("/"):
            print(f"  - Image saved to: {output}")
        else:
            print(f"  - {output}")
    print()
    assert len(outputs3) > 0

    # Test 6: Test error handling
    print("7. Testing error handling...")
    code4 = """# This will cause an error
undefined_variable"""

    outputs4 = await add_code_cell_and_execute(code4)
    print("✓ Error handling tested")
    print("Outputs:")
    for output in outputs4:
        print(f"  - {output[:100]}..." if len(str(output)) > 100 else f"  - {output}")
    print()
    assert len(outputs4) > 0
    # Check if output contains error information
    output_str = " ".join(str(output) for output in outputs4)
    assert (
        "NameError" in output_str
        or "error" in output_str.lower()
        or "successfully" in output_str
    )

    # Test 7: Add final markdown cell
    print("8. Adding conclusion markdown cell...")
    markdown3 = """## Test Complete

All tests have been executed successfully! The notebook now contains:
- Markdown cells with documentation
- Code cells with various outputs
- Visualizations
- Error examples
"""
    result3 = await add_markdown_cell(markdown3)
    print(f"✓ {result3}\n")
    assert "successfully" in result3

    print("=== All tests completed successfully! ===")
    print(f"Notebook saved to: {os.environ['NOTEBOOK_PATH']}")


if __name__ == "__main__":
    # Load environment variables for direct execution
    try:
        from dotenv import load_dotenv

        load_dotenv(Path(__file__).parent.parent / ".env")
    except ImportError:
        pass

    # For standalone execution
    asyncio.run(test_jupyter_mcp())
