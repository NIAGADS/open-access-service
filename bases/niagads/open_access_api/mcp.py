from fastapi import FastAPI, Request
from fastmcp import FastMCP
from fastmcp.utilities.lifespan import combine_lifespans
from niagads.open_access_api.constants import EBI_OLS_MCP_URL
from niagads.open_access_api.mcp_tools.ontology import (
    add_ols_ontology_search,
)
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
    if request.url.path.startswith("/mcp"):
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
    mcp_app = mcp.http_app(path="/mcp")

    # temp fix: SlowAPI requires a name
    mcp_app.__name__ = "open_access_mcp"

    # add tools
    add_ols_ontology_search(mcp)

    # add additional lifespan
    app.router.lifespan_context = combine_lifespans(
        app.router.lifespan_context,
        mcp_app.lifespan,
    )

    # FIXME: added as route instead of mounted to deal w/ trailing slash redirect issue
    # need to keep an eye on FastAPI documentation and/or develop `combined app` solution
    app.add_route(
        "/mcp",
        mcp_app,
        methods=["GET", "POST", "DELETE"],
        include_in_schema=False,
    )

    # add rate-limit middleware
    app.middleware("http")(mcp_rate_limit)

    # add openapi documentation
    app.openapi()["paths"]["/mcp"] = {
        "post": {
            "tags": ["MCP"],
            "summary": "Send MCP protocol messages",
            "description": (
                "Connect using an MCP-compatible client over Streamable HTTP. "
                "Initialize a session before calling tools. "
                "Swagger UI does not perform the MCP handshake automatically."
            ),
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {"type": "object"},
                        "description": "MCP JSON-RPC message.",
                    }
                },
            },
            "responses": {
                "200": {"description": "MCP JSON-RPC or event-stream response."},
                "202": {"description": "Message accepted without a response body."},
            },
        }
    }
