import json
from functools import partial
from pathlib import Path
from typing import AsyncGenerator

import pytest
from fastapi.testclient import TestClient
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
from httpx2 import ASGITransport, AsyncClient
from niagads.open_access_api.app import app


@pytest.fixture
def client(request):
    options = {"client": request.param} if hasattr(request, "param") else {}
    with TestClient(app, **options) as test_client:
        yield test_client


@pytest.fixture
async def open_access_mcp() -> AsyncGenerator[Client, None]:
    """Connect to the configured MCP endpoint with the app's resources initialized."""
    async with app.router.lifespan_context(app):
        transport = StreamableHttpTransport(
            "http://testserver/mcp",
            httpx_client_factory=partial(AsyncClient, transport=ASGITransport(app=app)),
        )
        async with Client(transport, timeout=30, init_timeout=15) as mcp_client:
            yield mcp_client


@pytest.fixture
def example_gene_record_mapping_response():
    path = Path(__file__).parent / "data" / "gene_record_mapping_response.json"
    return json.loads(path.read_text())
