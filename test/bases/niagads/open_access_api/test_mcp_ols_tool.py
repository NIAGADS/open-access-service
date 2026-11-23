"""Live integration test for the EBI-OLS MCP search tool."""

import json

import pytest

pytestmark = [
    pytest.mark.anyio,
    pytest.mark.parametrize("anyio_backend", ["asyncio"]),
]


async def test_ols_ontology_search_live(open_access_mcp):
    """Discover and execute OLS search through the configured Open Access app."""
    tools = {tool.name: tool for tool in await open_access_mcp.list_tools()}
    assert {
        "getGene",
        "getFeatureLocation",
        "searchOlsOntologies",
    } <= tools.keys(), list(tools.keys())

    schema = tools["searchOlsOntologies"].input_schema
    assert "query" in schema["required"]
    assert schema["properties"]["query"]["type"] == "string"
    assert schema["properties"]["includeObsoleteEntities"]["type"] == "boolean"

    result = await open_access_mcp.call_tool(
        "searchOlsOntologies",
        {"query": "Alzheimer", "includeObsoleteEntities": False},
    )

    assert not result.is_error
    payload = json.loads(result.content[0].text)
    assert payload
    assert any("alzheimer" in hit["title"].lower() for hit in payload)
    for hit in payload:
        assert hit["id"]
        assert hit["url"].startswith(("http://", "https://"))
        assert hit["isObsolete"] is False
