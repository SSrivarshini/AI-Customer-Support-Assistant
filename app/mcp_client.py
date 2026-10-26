import os
import sys
from pathlib import Path

from langchain_mcp_adapters.client import MultiServerMCPClient

from app.config import MCP_ENV_KEYS

ROOT = Path(__file__).resolve().parent.parent


async def load_mcp_tools():
    """Start the MCP servers (stdio) and return their tools as LangChain tools."""
    env = {k: os.environ[k] for k in MCP_ENV_KEYS if k in os.environ}
    client = MultiServerMCPClient(
        {
            "orders": {
                "command": sys.executable,
                "args": [str(ROOT / "mcp_servers" / "orders_server.py")],
                "transport": "stdio",
                "env": env,
            },
            "calendar": {
                "command": sys.executable,
                "args": [str(ROOT / "mcp_servers" / "calendar_server.py")],
                "transport": "stdio",
                "env": env,
            },
        }
    )
    return await client.get_tools()
