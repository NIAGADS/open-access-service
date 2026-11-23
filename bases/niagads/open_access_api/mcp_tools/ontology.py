from fastmcp import FastMCP
from fastmcp.server import create_proxy
from fastmcp.server.providers.proxy import ProxyClient
from fastmcp.server.transforms import ToolTransform
from fastmcp.tools.tool_transform import ToolTransformConfig
from niagads.open_access_api.constants import EBI_OLS_MCP_URL


def add_ols_ontology_search(mcp: FastMCP) -> None:
    """Expose EBI-OLS search through the MCP server."""
    # FIXME: do not hard-code timeout; create config constant
    ols = create_proxy(ProxyClient(EBI_OLS_MCP_URL, mode="legacy", timeout=30))
    ols.add_transform(
        ToolTransform(
            {
                "search": ToolTransformConfig(
                    name="searchOlsOntologies",
                ),
            }
        )
    )
    ols.enable(names={"searchOlsOntologies"}, only=True)
    mcp.mount(ols)
