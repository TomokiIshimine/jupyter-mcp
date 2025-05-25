import asyncio
import json
import uuid
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, urlunparse

import aiohttp
import nbformat
import websockets
from jupyter_ydoc import YNotebook

from config import config
from exceptions import KernelError, NotebookError, ServerConnectionError
from utils import clean_notebook_for_nbformat


class JupyterServerClient:
    """Handles communication with Jupyter server."""

    def __init__(self, server_url: str, token: str):
        self.server_url = server_url
        self.token = token
        self._session = None

    @property
    def headers(self) -> Dict[str, str]:
        """Get authorization headers for API requests."""
        return {"Authorization": f"token {self.token}"}

    async def _make_request(
        self, method: str, url: str, **kwargs
    ) -> aiohttp.ClientResponse:
        """Make an HTTP request with error handling."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method, url, headers=self.headers, **kwargs
                ) as resp:
                    return resp
        except aiohttp.ClientError as e:
            raise ServerConnectionError(f"Failed to connect to Jupyter server: {e}")

    async def get_kernelspecs(self) -> Dict[str, Any]:
        """Get available kernel specifications from server."""
        url = f"{self.server_url}/api/kernelspecs"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    raise KernelError(f"Failed to get kernelspecs: {resp.status}")

    async def get_notebook_content(self, notebook_path: str) -> Dict[str, Any]:
        """Get notebook content from server."""
        url = f"{self.server_url}/api/contents/{notebook_path}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as resp:
                if resp.status == 200:
                    return await resp.json()
                elif resp.status == 404:
                    raise NotebookError(f"Notebook not found: {notebook_path}")
                else:
                    raise NotebookError(f"Failed to access notebook: {resp.status}")

    async def save_notebook_content(
        self, notebook_path: str, notebook: nbformat.NotebookNode
    ) -> None:
        """Save notebook content to server."""
        url = f"{self.server_url}/api/contents/{notebook_path}"
        data = {
            "type": "notebook",
            "format": "json",
            "content": notebook,
        }
        async with aiohttp.ClientSession() as session:
            async with session.put(url, headers=self.headers, json=data) as resp:
                if resp.status not in [200, 201]:
                    raise NotebookError(f"Failed to save notebook: {resp.status}")

    async def get_sessions(self) -> List[Dict[str, Any]]:
        """Get active sessions from server."""
        url = f"{self.server_url}/api/sessions"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=self.headers) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    raise KernelError(f"Failed to get sessions: {resp.status}")

    async def create_session(
        self, notebook_path: str, kernel_name: str
    ) -> Dict[str, Any]:
        """Create a new session for the notebook."""
        url = f"{self.server_url}/api/sessions"
        data = {
            "path": notebook_path,
            "type": "notebook",
            "kernel": {"name": kernel_name},
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=self.headers, json=data) as resp:
                if resp.status in [200, 201]:
                    return await resp.json()
                else:
                    raise KernelError(f"Failed to create session: {resp.status}")


class KernelManager:
    """Manages kernel operations and execution."""

    def __init__(self, server_client: JupyterServerClient):
        self.server_client = server_client
        self.available_kernels: Dict[str, Any] = {}
        self.default_kernel: Optional[str] = None

    async def initialize_kernels(self) -> None:
        """Initialize available kernels and set default."""
        data = await self.server_client.get_kernelspecs()
        self.available_kernels = data.get("kernelspecs", {})

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
                self.default_kernel = next(iter(self.available_kernels.keys()))

    def get_kernel_name(self) -> str:
        """Get the kernel name to use, preferring environment variable if set."""
        if config.kernel_name:
            return config.kernel_name
        return self.default_kernel or "python3"

    async def get_or_create_session(self, notebook_path: str) -> tuple[str, str]:
        """Get existing session or create new one. Returns (session_id, kernel_id)."""
        sessions = await self.server_client.get_sessions()

        # Check for existing session
        for session in sessions:
            if session.get("notebook", {}).get("path") == notebook_path:
                return session["id"], session["kernel"]["id"]

        # Create new session
        kernel_name = self.get_kernel_name()
        session_data = await self.server_client.create_session(
            notebook_path, kernel_name
        )
        return session_data["id"], session_data["kernel"]["id"]

    async def execute_code(
        self, code: str, session_id: str, kernel_id: str
    ) -> List[Dict[str, Any]]:
        """Execute code in kernel and return outputs."""
        kernel_url = f"{self.server_client.server_url}/api/kernels/{kernel_id}"
        ws_url = f"{kernel_url.replace('http', 'ws')}/channels?token={self.server_client.token}"

        try:
            async with websockets.connect(ws_url) as ws:
                msg_id = str(uuid.uuid4())
                execute_request = self._create_execute_request(code, msg_id, session_id)
                await ws.send(json.dumps(execute_request))
                return await self._collect_outputs(ws, msg_id)
        except websockets.exceptions.WebSocketException as e:
            raise KernelError(f"WebSocket error during kernel execution: {e}")

    def _create_execute_request(
        self, code: str, msg_id: str, session_id: str
    ) -> Dict[str, Any]:
        """Create execute request message."""
        return {
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

    async def _collect_outputs(
        self, ws: websockets.WebSocketServerProtocol, msg_id: str
    ) -> List[Dict[str, Any]]:
        """Collect outputs from kernel execution."""
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
                        "execution_count": msg["content"]["execution_count"],
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

        return outputs


class NotebookManager:
    """Manages notebook operations using YDoc and nbformat."""

    def __init__(self, notebook_path: str, server_url: str, token: str):
        self.notebook_path = notebook_path
        self.server_client = JupyterServerClient(server_url, token)
        self.kernel_manager = KernelManager(self.server_client)
        self.ydoc: Optional[YNotebook] = None
        self._lock = asyncio.Lock()
        self.notebook: Optional[nbformat.NotebookNode] = None

    def _get_websocket_url(self) -> str:
        """Convert HTTP URL to WebSocket URL for YDoc connection."""
        parsed = urlparse(self.server_client.server_url)
        ws_scheme = "wss" if parsed.scheme == "https" else "ws"
        return urlunparse(
            (
                ws_scheme,
                parsed.netloc,
                f"/api/collaboration/room/json:notebook:{self.notebook_path}",
                "",
                f"token={self.server_client.token}",
                "",
            )
        )

    async def get_available_kernels(self) -> Dict[str, Any]:
        """Get available kernels from Jupyter server."""
        await self.kernel_manager.initialize_kernels()
        return self.kernel_manager.available_kernels

    async def get_kernel_name(self) -> str:
        """Get the kernel name to use."""
        if not self.kernel_manager.default_kernel:
            await self.kernel_manager.initialize_kernels()
        return self.kernel_manager.get_kernel_name()

    async def initialize(self) -> None:
        """Initialize the notebook manager."""
        async with self._lock:
            await self.kernel_manager.initialize_kernels()
            await self._load_or_create_notebook()
            self._initialize_ydoc()

    async def _load_or_create_notebook(self) -> None:
        """Load existing notebook or create new one."""
        try:
            data = await self.server_client.get_notebook_content(self.notebook_path)
            notebook_content = data.get("content", {})
            cleaned_content = clean_notebook_for_nbformat(notebook_content)
            self.notebook = nbformat.from_dict(cleaned_content)
        except NotebookError as e:
            if "not found" in str(e):
                # Create new notebook
                self.notebook = nbformat.v4.new_notebook()
                await self.save_notebook_to_server()
            else:
                raise

    def _initialize_ydoc(self) -> None:
        """Initialize YDoc for collaborative editing."""
        self.ydoc = YNotebook()
        if self.notebook:
            self.ydoc.set(self.notebook)

    async def save_notebook_to_server(self) -> None:
        """Save the notebook to Jupyter server."""
        if self.notebook:
            await self.server_client.save_notebook_content(
                self.notebook_path, self.notebook
            )

    async def save_notebook(self) -> None:
        """Save the notebook to server."""
        await self.save_notebook_to_server()

    async def sync_from_ydoc(self) -> None:
        """Sync notebook from YDoc."""
        if self.ydoc:
            notebook_dict = self.ydoc.get()
            if notebook_dict:
                self.notebook = nbformat.from_dict(notebook_dict)

    async def sync_to_ydoc(self) -> None:
        """Sync notebook to YDoc."""
        if self.ydoc and self.notebook:
            self.ydoc.set(self.notebook)

    async def refresh_from_server(self) -> None:
        """Refresh notebook content from Jupyter server."""
        data = await self.server_client.get_notebook_content(self.notebook_path)
        notebook_content = data.get("content", {})
        cleaned_content = clean_notebook_for_nbformat(notebook_content)
        self.notebook = nbformat.from_dict(cleaned_content)

        # Update YDoc with the latest content
        if self.ydoc:
            self.ydoc.set(self.notebook)

    async def execute_on_server(self, cell_index: int) -> Dict[str, Any]:
        """Execute a cell on the Jupyter server."""
        if not self.notebook or cell_index >= len(self.notebook.cells):
            raise NotebookError(f"Invalid cell index: {cell_index}")

        session_id, kernel_id = await self.kernel_manager.get_or_create_session(
            self.notebook_path
        )

        code = self.notebook.cells[cell_index].source
        outputs = await self.kernel_manager.execute_code(code, session_id, kernel_id)

        return {"outputs": outputs}
