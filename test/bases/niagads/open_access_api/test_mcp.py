"""Test MCP tool discovery and execution against the Open Access API routes."""

import pytest
from niagads.common.genomic.regions.models import OneBasedGenomicRegion

pytestmark = [
    pytest.mark.anyio,
    pytest.mark.parametrize("anyio_backend", ["asyncio"]),
]


async def test_mcp_tools(open_access_mcp):
    tools = await open_access_mcp.list_tools()

    names = {tool.name for tool in tools}
    assert {"getGene", "getFeatureLocation"} <= names
    assert "root" not in names


@pytest.mark.parametrize("flank", [0, 25])
async def test_mcp_tool_execution(
    open_access_mcp, example_gene_record_mapping_response, flank
):
    location = OneBasedGenomicRegion.from_region_id(
        example_gene_record_mapping_response["data"]["APOE"][0]["location"]
    )

    result = await open_access_mcp.call_tool(
        "getFeatureLocation", {"id": "APOE", "flank": flank}
    )

    assert not result.is_error
    assert result.data == {
        "chr": str(location.chromosome),
        "start": location.start - flank,
        "end": location.end + flank,
    }
