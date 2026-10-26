"""The gallery an MCP Apps host draws beside a search.

A tool can carry a UI resource: the host opens it in a sandboxed iframe and pushes
the tool's result in, which is what turns "six results with URLs" into a row of
pictures inside the conversation. Clients that do not implement the extension get
the same answer as text and lose nothing.

The HTML lives beside this module and is served as-is. The policy is built from
the delivery base rather than written out by hand, so moving the account moves the
allowlist with it: an asset from another host would be blocked, and the widget
would be silently empty.
"""

from pathlib import Path
from urllib.parse import urlsplit

from fastmcp.apps import AppConfig, ResourceCSP

from app.mcp.server import mcp
from app.settings import settings

GALLERY_URI = "ui://genblocks/gallery.html"

# The helper that speaks to the host, published on unpkg so the widget needs no
# build step of its own. It is a delivery origin, not a dependency of the server.
SDK_ORIGIN = "https://unpkg.com"

GALLERY = Path(__file__).with_name("ui") / "gallery.html"


def resource_domains() -> list[str]:
    """What the iframe may load: our own pictures, and the host's helper."""
    base = urlsplit(settings.asset_base_url)
    if not base.scheme or not base.netloc:
        return [SDK_ORIGIN]

    return [f"{base.scheme}://{base.netloc}", SDK_ORIGIN]


@mcp.resource(
    GALLERY_URI,
    app=AppConfig(csp=ResourceCSP(resource_domains=resource_domains())),
)
def gallery() -> str:
    """The gallery: the search's results as pictures, with a caption and a link."""
    return GALLERY.read_text(encoding="utf-8")
