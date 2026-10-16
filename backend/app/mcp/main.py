"""ASGI entrypoint for the MCP service.

    uvicorn app.mcp.main:app --host 0.0.0.0 --port 8001

``stateless_http`` is on because MCP clients (Claude Code, Cursor, ChatGPT) do
not forward cookies, so a load balancer cannot pin them to the instance holding
their session. Without it the server only works as a single instance.
"""

from app.mcp import tools  # noqa: F401  (importing it registers the tools)
from app.mcp.server import mcp

app = mcp.http_app(stateless_http=True)
