#!/usr/bin/env python3
"""
Test script to verify that manually deleted cells don't reappear
"""

import asyncio
import os
import sys
from pathlib import Path

import pytest

# Add project root to Python path for direct execution
if __name__ == "__main__":
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

# Import from src package - conftest.py handles path setup for pytest
from src.tools import (
    add_code_cell_and_execute,
    delete_cell,
    get_all_cells,
    notebook_manager,
)


@pytest.mark.asyncio
async def test_deletion_sync():
    """Test that manually deleted cells don't reappear."""
    print("=== Testing Cell Deletion Synchronization ===\n")

    # Update notebook path for this test to use a fresh notebook
    os.environ["NOTEBOOK_PATH"] = "deletion_test.ipynb"

    # Reinitialize notebook manager with new path
    notebook_manager.notebook_path = "deletion_test.ipynb"

    # Initialize notebook manager
    print("1. Initializing notebook manager...")
    await notebook_manager.initialize()
    print("✓ Notebook manager initialized\n")

    # Get initial cell count
    initial_cells = await get_all_cells()
    initial_count = len(initial_cells)
    print(f"Initial cell count: {initial_count}")

    # Step 1: Add first code cell
    print("2. Adding first code cell...")
    code1 = """# First cell
print("This is the first cell")
x = 100"""
    await add_code_cell_and_execute(code1)
    print("✓ First cell added\n")

    # Step 2: Add second code cell
    print("3. Adding second code cell...")
    code2 = """# Second cell
print("This is the second cell")
y = 200"""
    await add_code_cell_and_execute(code2)
    print("✓ Second cell added\n")

    # Step 3: Get all cells
    print("4. Getting all cells...")
    cells = await get_all_cells()
    expected_count = initial_count + 2
    print(f"✓ Total cells: {len(cells)} (expected: {expected_count})")

    # Find our test cells
    first_cell_index = None
    second_cell_index = None
    for i, cell in enumerate(cells):
        if "This is the first cell" in cell["source"]:
            first_cell_index = i
        elif "This is the second cell" in cell["source"]:
            second_cell_index = i

    print(f"First test cell at index: {first_cell_index}")
    print(f"Second test cell at index: {second_cell_index}")
    print()

    assert first_cell_index is not None, "First test cell not found"
    assert second_cell_index is not None, "Second test cell not found"
    assert len(cells) == expected_count

    # Step 4: Simulate manual deletion by using delete_cell
    print("5. Simulating manual deletion of first test cell...")
    await delete_cell(first_cell_index)
    print("✓ First test cell deleted\n")

    # Step 5: Get cells after deletion
    print("6. Getting cells after deletion...")
    cells_after_delete = await get_all_cells()
    print(
        f"✓ Total cells after deletion: {len(cells_after_delete)} (expected: {expected_count - 1})"
    )

    # Verify first cell is gone
    first_cell_found_after_delete = any(
        "This is the first cell" in cell["source"] for cell in cells_after_delete
    )
    assert (
        not first_cell_found_after_delete
    ), "First test cell still exists after deletion"
    assert len(cells_after_delete) == expected_count - 1

    # Step 6: Add a new cell
    print("7. Adding a new cell after deletion...")
    code3 = """# Third cell (added after deletion)
print("This is the third cell")
z = 300"""
    await add_code_cell_and_execute(code3)
    print("✓ Third cell added\n")

    # Step 7: Get final cells
    print("8. Getting final cells...")
    final_cells = await get_all_cells()
    final_expected_count = expected_count  # initial + 2 - 1 + 1 = initial + 2
    print(f"✓ Total final cells: {len(final_cells)} (expected: {final_expected_count})")

    # Verify that the first cell didn't reappear
    print("9. Verifying results...")
    first_cell_found = any(
        "This is the first cell" in cell["source"] for cell in final_cells
    )
    second_cell_found = any(
        "This is the second cell" in cell["source"] for cell in final_cells
    )
    third_cell_found = any(
        "This is the third cell" in cell["source"] for cell in final_cells
    )

    assert not first_cell_found, "ERROR: The deleted first cell reappeared!"
    assert second_cell_found, "ERROR: The second cell disappeared!"
    assert third_cell_found, "ERROR: The third cell was not added!"
    assert len(final_cells) == final_expected_count

    print("✓ SUCCESS: The deleted first cell did not reappear!")
    print("✓ Only the second and third cells are present.")


if __name__ == "__main__":
    # Load environment variables for direct execution
    try:
        from dotenv import load_dotenv

        load_dotenv(Path(__file__).parent.parent / ".env")
    except ImportError:
        pass

    # For standalone execution
    asyncio.run(test_deletion_sync())
