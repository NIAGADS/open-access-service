"""Print the production NIAGADS MCP tool definitions as JSON."""

import asyncio
import json

from fastmcp import Client


async def main() -> None:
    """Discover production MCP tools and write their definitions to stdout."""
    async with Client("https://api.niagads.org/api/mcp") as client:
        tools = await client.list_tools()
        print(
            json.dumps(
                [tool.model_dump(mode="json", by_alias=True) for tool in tools],
                indent=2,
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
