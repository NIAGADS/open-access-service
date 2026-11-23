from fastmcp import FastMCP
from fastmcp.server import create_proxy
from fastmcp.server.transforms import ToolTransform
from fastmcp.tools.tool_transform import ToolTransformConfig
from niagads.open_access_api.constants import EBI_OLS_MCP_URL


def add_ols_ontology_search(mcp: FastMCP) -> None:
    """Expose EBI-OLS search through the MCP server."""
    ols = create_proxy(EBI_OLS_MCP_URL, mode="legacy")
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
