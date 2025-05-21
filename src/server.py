import os
from dataclasses import dataclass
from pathlib import Path

from mcp.server.fastmcp import FastMCP


@dataclass
class AppConfig:
    """Application configuration."""

    notebook_path: str = os.getenv("NOTEBOOK_PATH", "notebook.ipynb")
    server_url: str = os.getenv("SERVER_URL", "http://localhost:8888")
    token: str = os.getenv("TOKEN", "MY_TOKEN")
    mcp_image_dir: Path = Path(os.getenv("MCP_IMAGE_DIR", "mcp_images"))

    def __post_init__(self):
        self.mcp_image_dir.mkdir(exist_ok=True)


config = AppConfig()

mcp = FastMCP("jupyter-mcp-server")


@mcp.tool()
async def test(text: str) -> str:
    return f"Hello, {text}!"


if __name__ == "__main__":
    mcp.run()
