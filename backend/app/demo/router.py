"""The playground endpoint.

Public on purpose. An anonymous visitor is the interesting case here: the page
exists to show what the MCP door does when nobody is signed in, so a route that
demanded a token would hide the half of the story worth telling.

It is also the only endpoint on this API that accepts a caller without a token,
and it does nothing with one except pass it to the MCP server. No domain rule
runs behind it.
"""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.authz.dependencies import get_optional_first_party_token
from app.demo.runner import run_demo
from app.demo.schemas import DemoRun, DemoRunRequest

demo_router = APIRouter(prefix="/demo", tags=["demo"])


@demo_router.post("/run", response_model=DemoRun)
async def run(
    request: DemoRunRequest,
    token: Annotated[str | None, Depends(get_optional_first_party_token)],
) -> DemoRun:
    """Run the demo agent once, with the caller's token when there is one."""
    return await run_demo(
        token=token,
        thread_id=request.thread_id,
        decision=request.decision,
    )
