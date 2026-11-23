import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from fastmcp import FastMCP
from niagads.open_access_api.app import app


@pytest.fixture
def client(request):
    options = {"client": request.param} if hasattr(request, "param") else {}
    with TestClient(app, **options) as test_client:
        yield test_client


@pytest.fixture
def mcp() -> FastMCP:
    """Build an in-process MCP server from the API's registered routes."""
    return FastMCP.from_fastapi(app=app)


@pytest.fixture
def example_gene_record_mapping_response():
    path = Path(__file__).parent / "data" / "gene_record_mapping_response.json"
    return json.loads(path.read_text())
