import asyncio

from .tools import mcp, notebook_manager


async def startup():
    """Initialize the notebook manager on startup."""
    await notebook_manager.initialize()


if __name__ == "__main__":
    # Run startup before starting the MCP server
    asyncio.run(startup())
    mcp.run()
