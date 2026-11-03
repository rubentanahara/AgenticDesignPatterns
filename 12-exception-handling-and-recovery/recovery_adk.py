import asyncio

from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.adk.tools import ToolContext
from google.adk.workflow import START, Workflow

from step_logger import phase, show, show_event

MODEL = "gemini-3.5-flash-lite"


def get_precise_location_info(address: str, tool_context: ToolContext) -> dict:
    """Looks up exact coordinates for a street address."""
    tool_context.state["primary_location_failed"] = True
    return {"status": "error", "message": "Geocoding service unavailable"}


def get_general_area_info(city: str, tool_context: ToolContext) -> dict:
    """Returns approximate information about a city."""
    tool_context.state["location_result"] = f"{city}: approximate city-level area"
    return {"status": "ok", "area": f"{city}, approximate"}


primary = Agent(
    name="PrimaryHandler",
    model=MODEL,
    instruction="Call get_precise_location_info with the user's address.",
    tools=[get_precise_location_info],
)

fallback = Agent(
    name="FallbackHandler",
    model=MODEL,
    instruction=(
        "primary_location_failed = {primary_location_failed?}. If it is True, extract the city from the "
        "user's query and call get_general_area_info. Otherwise do nothing."
    ),
    tools=[get_general_area_info],
)

responder = Agent(
    name="ResponseAgent",
    model=MODEL,
    instruction=(
        "Location result: {location_result?}. Present it clearly, and say it is approximate if so. "
        "If it is empty, apologize that the location could not be retrieved."
    ),
)

robust_location_agent = Workflow(name="RobustLocation", edges=[(START, primary, fallback, responder)])


if __name__ == "__main__":
    phase("Recovery: primary, fallback, response")
    show("initial prompt", "Where is 10 Main St, Springfield?")
    events = asyncio.run(InMemoryRunner(node=robust_location_agent).run_debug("Where is 10 Main St, Springfield?", quiet=True))
    for event in events:
        phase(f"{event.author}")
        show_event(event)
