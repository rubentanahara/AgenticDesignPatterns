import asyncio
import sys
from pathlib import Path

from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams
from mcp import StdioServerParameters

from step_logger import phase, show, show_event

MODEL = "gemini-3.5-flash-lite"
SERVER_SCRIPT = str(Path(__file__).with_name("tickets_server.py"))

tickets = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(command=sys.executable, args=[SERVER_SCRIPT]),
    ),
    tool_filter=["search_tickets"],
)

agent = LlmAgent(
    name="TriageAgent",
    model=MODEL,
    instruction="Help the user triage support tickets using the ticket tools.",
    tools=[tickets],
)


async def main() -> None:
    phase("Agent discovers MCP tools, calls them, answers")
    show("initial prompt", "Summarize the open high-priority tickets.")
    events = await InMemoryRunner(agent=agent).run_debug("Summarize the open high-priority tickets.", quiet=True)
    for event in events:
        show_event(event)
    phase("Done")


if __name__ == "__main__":
    asyncio.run(main())
