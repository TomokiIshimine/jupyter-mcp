import os
from dataclasses import dataclass
from pathlib import Path

from exceptions import ConfigurationError


@dataclass
class AppConfig:
    """Application configuration."""

    notebook_path: str = os.getenv("NOTEBOOK_PATH", "notebook.ipynb")
    server_url: str = os.getenv("SERVER_URL", "http://localhost:8888")
    token: str = os.getenv("TOKEN", "")
    kernel_name: str = os.getenv("KERNEL_NAME", "")
    mcp_image_dir: Path = Path(os.getenv("MCP_IMAGE_DIR", "mcp_images"))
    timeout: int = int(os.getenv("TIMEOUT", 180))
    startup_timeout: int = int(os.getenv("STARTUP_TIMEOUT", 60))

    def __post_init__(self):
        self.mcp_image_dir.mkdir(exist_ok=True)
        if not self.token:
            raise ConfigurationError(
                "TOKEN environment variable must be set to connect to Jupyter Server"
            )
