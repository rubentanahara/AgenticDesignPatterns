import asyncio
import warnings

from google.adk.agents import Agent
from google.adk.agents.context_cache_config import ContextCacheConfig
from google.adk.apps import App
from google.adk.runners import InMemoryRunner

from step_logger import phase, show, show_event

warnings.filterwarnings("ignore", message=".*GeminiContextCacheManager.*")

MODEL = "gemini-3.5-flash-lite"
REQUESTS = ["Book me a hotel in Paris.", "What is the highest mountain in the world?", "Do the thing."]


def book(request: str) -> str:
    """Books flights and hotels for the user."""
    return f"Simulated booking for: {request}"


def lookup(question: str) -> str:
    """Answers general information questions."""
    return f"Simulated lookup for: {question}"


booker = Agent(
    name="Booker",
    model=MODEL,
    description="Handles all flight and hotel booking requests.",
    tools=[book],
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)

info = Agent(
    name="Info",
    model=MODEL,
    description="Answers general information questions.",
    tools=[lookup],
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)

clarifier = Agent(
    name="Clarifier",
    model=MODEL,
    description="Handles vague requests that fit neither booking nor a general question.",
    instruction="Ask the user one short question to find out what they need. Do not guess.",
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)

coordinator = Agent(
    name="Coordinator",
    model=MODEL,
    instruction=(
        "Never answer directly. Delegate bookings to Booker, general questions to Info, "
        "and vague or unclear requests to Clarifier."
    ),
    sub_agents=[booker, info, clarifier],
)


if __name__ == "__main__":
    phase("Routing: coordinator delegates to a specialist agent")
    show("initial prompt", REQUESTS)
    runner = InMemoryRunner(app=App(name="router", root_agent=coordinator, context_cache_config=ContextCacheConfig()))
    events = []
    for number, request in enumerate(REQUESTS):
        events += asyncio.run(runner.run_debug(request, session_id=f"request-{number}", quiet=True))
    for event in events:
        show_event(event)
    phase("Routing done")
