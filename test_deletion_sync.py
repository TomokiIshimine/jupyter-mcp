#!/usr/bin/env python3
"""
Test script to verify that manually deleted cells don't reappear
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set environment variables
os.environ["SERVER_URL"] = "http://host.docker.internal:8888"
os.environ["TOKEN"] = "my-token"
os.environ["NOTEBOOK_PATH"] = "deletion_test.ipynb"
os.environ["MCP_IMAGE_DIR"] = "test_images"

# Import after setting environment variables
from server import (
    add_code_cell_and_execute,
    delete_cell,
    get_all_cells,
    notebook_manager,
)


async def test_deletion_sync():
    """Test that manually deleted cells don't reappear."""
    print("=== Testing Cell Deletion Synchronization ===\n")

    try:
        # Initialize notebook manager
        print("1. Initializing notebook manager...")
        await notebook_manager.initialize()
        print("✓ Notebook manager initialized\n")

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
        print(f"✓ Total cells: {len(cells)}")
        for i, cell in enumerate(cells):
            print(f"   Cell {i}: {cell['source'][:50]}...")
        print()

        # Step 4: Simulate manual deletion by using delete_cell
        print("5. Simulating manual deletion of first cell...")
        await delete_cell(0)
        print("✓ First cell deleted\n")

        # Step 5: Get cells after deletion
        print("6. Getting cells after deletion...")
        cells_after_delete = await get_all_cells()
        print(f"✓ Total cells after deletion: {len(cells_after_delete)}")
        for i, cell in enumerate(cells_after_delete):
            print(f"   Cell {i}: {cell['source'][:50]}...")
        print()

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
        print(f"✓ Total final cells: {len(final_cells)}")
        for i, cell in enumerate(final_cells):
            print(f"   Cell {i}: {cell['source'][:50]}...")
        print()

        # Verify that the first cell didn't reappear
        print("9. Verifying results...")
        first_cell_found = any(
            "This is the first cell" in cell["source"] for cell in final_cells
        )
        if first_cell_found:
            print("❌ ERROR: The deleted first cell reappeared!")
            return False
        else:
            print("✓ SUCCESS: The deleted first cell did not reappear!")
            print("✓ Only the second and third cells are present.")
            return True

    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Main function."""
    success = await test_deletion_sync()
    print("\n=== Test completed ===")
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
