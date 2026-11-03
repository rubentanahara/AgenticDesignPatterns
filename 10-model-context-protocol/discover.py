import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters, stdio_client
from mcp.types import TextContent

from step_logger import phase, show

SERVER = StdioServerParameters(command=sys.executable, args=[str(Path(__file__).with_name("tickets_server.py"))])


async def main() -> None:
    async with stdio_client(SERVER) as (read, write), ClientSession(read, write) as session:
        phase("Discovery")
        await session.initialize()
        show("tools", [tool.name for tool in (await session.list_tools()).tools])
        show("prompts", [prompt.name for prompt in (await session.list_prompts()).prompts])
        phase("Tool call: search_tickets")
        show("arguments", {"priority": "high"}, "yellow")
        result = await session.call_tool("search_tickets", {"priority": "high"})
        phase("Result")
        first = result.content[0]
        assert isinstance(first, TextContent)
        show("high + open", first.text, "magenta")


if __name__ == "__main__":
    asyncio.run(main())
