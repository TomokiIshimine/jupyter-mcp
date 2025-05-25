import asyncio
import json
import uuid
from typing import Any, Dict, Optional
from urllib.parse import urlparse, urlunparse

import aiohttp
import nbformat
import websockets
from jupyter_ydoc import YNotebook

from config import config
from exceptions import KernelError, NotebookError, ServerConnectionError
from utils import clean_notebook_for_nbformat


class NotebookManager:
    """Manages notebook operations using YDoc and nbformat."""

    def __init__(self, notebook_path: str, server_url: str, token: str):
        self.notebook_path = notebook_path
        self.server_url = server_url
        self.token = token
        self.ydoc: Optional[YNotebook] = None
        self._lock = asyncio.Lock()
        self.ws_connection = None
        self.available_kernels = {}
        self.default_kernel = None

    def _get_websocket_url(self) -> str:
        """Convert HTTP URL to WebSocket URL for YDoc connection."""
        parsed = urlparse(self.server_url)
        ws_scheme = "wss" if parsed.scheme == "https" else "ws"
        ws_url = urlunparse(
            (
                ws_scheme,
                parsed.netloc,
                f"/api/collaboration/room/json:notebook:{self.notebook_path}",
                "",
                f"token={self.token}",
                "",
            )
        )
        return ws_url

    async def get_available_kernels(self) -> Dict[str, Any]:
        """Get available kernels from Jupyter server."""
        try:
            async with aiohttp.ClientSession() as session:
                kernelspecs_url = f"{self.server_url}/api/kernelspecs"
                headers = {"Authorization": f"token {self.token}"}

                async with session.get(kernelspecs_url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self.available_kernels = data.get("kernelspecs", {})

                        # Set default kernel if not already set
                        if not self.default_kernel and self.available_kernels:
                            # Try to use the default kernel from server
                            default_name = data.get("default", None)
                            if default_name and default_name in self.available_kernels:
                                self.default_kernel = default_name
                            # Otherwise, prefer python3 if available
                            elif "python3" in self.available_kernels:
                                self.default_kernel = "python3"
                            # Otherwise, use the first available kernel
                            else:
                                self.default_kernel = next(
                                    iter(self.available_kernels.keys())
                                )

                        return self.available_kernels
                    else:
                        raise KernelError(f"Failed to get kernelspecs: {resp.status}")
        except aiohttp.ClientError as e:
            raise ServerConnectionError(f"Failed to connect to Jupyter server: {e}")

    async def get_kernel_name(self) -> str:
        """Get the kernel name to use, preferring environment variable if set."""
        # If kernel_name is set in environment, use it
        if config.kernel_name:
            return config.kernel_name

        # Otherwise, use the default kernel from server
        if not self.default_kernel:
            await self.get_available_kernels()

        return self.default_kernel or "python3"

    async def initialize(self):
        """Initialize the notebook manager."""
        async with self._lock:
            # Get available kernels first
            await self.get_available_kernels()

            # First, check if notebook exists on server
            try:
                async with aiohttp.ClientSession() as session:
                    # Get notebook content from server
                    notebook_url = (
                        f"{self.server_url}/api/contents/{self.notebook_path}"
                    )
                    headers = {"Authorization": f"token {self.token}"}

                    async with session.get(notebook_url, headers=headers) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            notebook_content = data.get("content", {})
                            # Clean the notebook content before using nbformat
                            cleaned_content = clean_notebook_for_nbformat(
                                notebook_content
                            )
                            self.notebook = nbformat.from_dict(cleaned_content)
                        elif resp.status == 404:
                            # Create new notebook
                            self.notebook = nbformat.v4.new_notebook()
                            await self.save_notebook_to_server()
                        else:
                            raise NotebookError(
                                f"Failed to access notebook: {resp.status}"
                            )
            except aiohttp.ClientError as e:
                raise ServerConnectionError(f"Failed to connect to Jupyter server: {e}")

            # Initialize YDoc for collaborative editing
            self.ydoc = YNotebook()
            # YDoc expects a notebook dict
            self.ydoc.set(self.notebook)

    async def save_notebook_to_server(self):
        """Save the notebook to Jupyter server."""
        try:
            async with aiohttp.ClientSession() as session:
                notebook_url = f"{self.server_url}/api/contents/{self.notebook_path}"
                headers = {"Authorization": f"token {self.token}"}

                # NotebookNode is dict-like, so we can use it directly
                data = {
                    "type": "notebook",
                    "format": "json",
                    "content": self.notebook,
                }

                async with session.put(
                    notebook_url, headers=headers, json=data
                ) as resp:
                    if resp.status not in [200, 201]:
                        raise NotebookError(f"Failed to save notebook: {resp.status}")
        except aiohttp.ClientError as e:
            raise ServerConnectionError(f"Failed to connect to Jupyter server: {e}")

    async def save_notebook(self):
        """Save the notebook to server."""
        # サーバーへの保存のみ実行（ローカル保存は削除）
        await self.save_notebook_to_server()

    async def sync_from_ydoc(self):
        """Sync notebook from YDoc."""
        if self.ydoc:
            # Get the notebook dict from YDoc
            notebook_dict = self.ydoc.get()
            if notebook_dict:
                self.notebook = nbformat.from_dict(notebook_dict)

    async def sync_to_ydoc(self):
        """Sync notebook to YDoc."""
        if self.ydoc:
            # YDoc expects a notebook dict
            self.ydoc.set(self.notebook)

    async def refresh_from_server(self):
        """Refresh notebook content from Jupyter server."""
        try:
            async with aiohttp.ClientSession() as session:
                notebook_url = f"{self.server_url}/api/contents/{self.notebook_path}"
                headers = {"Authorization": f"token {self.token}"}

                async with session.get(notebook_url, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        notebook_content = data.get("content", {})
                        # Clean the notebook content before using nbformat
                        cleaned_content = clean_notebook_for_nbformat(notebook_content)
                        self.notebook = nbformat.from_dict(cleaned_content)
                        # Update YDoc with the latest content
                        if self.ydoc:
                            self.ydoc.set(self.notebook)
                    else:
                        raise NotebookError(
                            f"Failed to refresh notebook: {resp.status}"
                        )
        except aiohttp.ClientError as e:
            raise ServerConnectionError(f"Failed to connect to Jupyter server: {e}")

    async def execute_on_server(self, cell_index: int) -> Dict[str, Any]:
        """Execute a cell on the Jupyter server."""
        try:
            async with aiohttp.ClientSession() as session:
                # Create a session and kernel
                sessions_url = f"{self.server_url}/api/sessions"
                headers = {"Authorization": f"token {self.token}"}

                # Check for existing session
                async with session.get(sessions_url, headers=headers) as resp:
                    sessions = await resp.json()
                    session_id = None
                    for s in sessions:
                        if s.get("notebook", {}).get("path") == self.notebook_path:
                            session_id = s["id"]
                            kernel_id = s["kernel"]["id"]
                            break

                # Create new session if needed
                if not session_id:
                    # Get the kernel name to use
                    kernel_name = await self.get_kernel_name()

                    data = {
                        "path": self.notebook_path,
                        "type": "notebook",
                        "kernel": {"name": kernel_name},
                    }
                    async with session.post(
                        sessions_url, headers=headers, json=data
                    ) as resp:
                        session_data = await resp.json()
                        session_id = session_data["id"]
                        kernel_id = session_data["kernel"]["id"]

                # Execute code via kernel
                kernel_url = f"{self.server_url}/api/kernels/{kernel_id}"
                ws_url = (
                    f"{kernel_url.replace('http', 'ws')}/channels?token={self.token}"
                )

                # Connect to kernel websocket
                async with websockets.connect(ws_url) as ws:
                    # Send execute request
                    code = self.notebook.cells[cell_index].source
                    msg_id = str(uuid.uuid4())

                    execute_request = {
                        "header": {
                            "msg_id": msg_id,
                            "msg_type": "execute_request",
                            "session": session_id,
                        },
                        "parent_header": {},
                        "metadata": {},
                        "content": {
                            "code": code,
                            "silent": False,
                            "store_history": True,
                            "user_expressions": {},
                            "allow_stdin": False,
                        },
                    }

                    await ws.send(json.dumps(execute_request))

                    # Collect outputs
                    outputs = []
                    while True:
                        msg = json.loads(await ws.recv())
                        msg_type = msg["header"]["msg_type"]

                        if msg["parent_header"].get("msg_id") != msg_id:
                            continue

                        if msg_type == "stream":
                            outputs.append(
                                {
                                    "output_type": "stream",
                                    "name": msg["content"]["name"],
                                    "text": msg["content"]["text"],
                                }
                            )
                        elif msg_type == "display_data":
                            outputs.append(
                                {
                                    "output_type": "display_data",
                                    "data": msg["content"]["data"],
                                    "metadata": msg["content"]["metadata"],
                                }
                            )
                        elif msg_type == "execute_result":
                            outputs.append(
                                {
                                    "output_type": "execute_result",
                                    "execution_count": msg["content"][
                                        "execution_count"
                                    ],
                                    "data": msg["content"]["data"],
                                    "metadata": msg["content"]["metadata"],
                                }
                            )
                        elif msg_type == "error":
                            outputs.append(
                                {
                                    "output_type": "error",
                                    "ename": msg["content"]["ename"],
                                    "evalue": msg["content"]["evalue"],
                                    "traceback": msg["content"]["traceback"],
                                }
                            )
                        elif msg_type == "execute_reply":
                            break

                    return {"outputs": outputs}
        except aiohttp.ClientError as e:
            raise ServerConnectionError(f"Failed to connect to Jupyter server: {e}")
        except websockets.exceptions.WebSocketException as e:
            raise KernelError(f"WebSocket error during kernel execution: {e}")
