from fastapi import FastAPI, Request
from fastmcp import FastMCP
from fastmcp.utilities.lifespan import combine_lifespans
from slowapi.util import get_remote_address


async def mcp_rate_limit(request: Request, call_next):
    """Record the client address for MCP requests before forwarding them.

    Args:
        request (Request): Incoming HTTP request.
        call_next (Callable): Async callable that forwards the request to the
            next handler.

    Returns:
        Response: Response returned by the next handler.
    """
    # TODO: check for an verify access token as alternative id
    if request.url.path.startswith("/mcp/"):
        client_id = get_remote_address(request)
        request.state.mcp_client_id = client_id

    return await call_next(request)


def configure_mcp(app: FastAPI) -> None:
    """Configure the MCP server, lifespan, and request middleware.

    Mount the MCP HTTP application at ``/mcp`` and combine its lifespan with
    the existing application lifespan.

    Args:
        app (FastAPI): Application whose registered routes are exposed through
            MCP and whose middleware and lifespan are updated in place.
    """
    mcp = FastMCP.from_fastapi(app=app)
    mcp_app = mcp.http_app(path="/")
    app.router.lifespan_context = combine_lifespans(
        app.router.lifespan_context,
        mcp_app.lifespan,
    )
    app.mount("/mcp", mcp_app)
    app.middleware("http")(mcp_rate_limit)
