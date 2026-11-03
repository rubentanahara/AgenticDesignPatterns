import asyncio

from google.adk.agents import LlmAgent
from google.adk.agents.remote_a2a_agent import AGENT_CARD_WELL_KNOWN_PATH, RemoteA2aAgent
from google.adk.runners import InMemoryRunner

from step_logger import phase, show, show_event

MODEL = "gemini-3.5-flash-lite"
WEATHER_AGENT_URL = "http://localhost:8001"

remote_weather = RemoteA2aAgent(
    name="weather_agent",
    description="Remote agent that provides tomorrow's weather forecast for a city.",
    agent_card=f"{WEATHER_AGENT_URL}{AGENT_CARD_WELL_KNOWN_PATH}",
)

trip_planner = LlmAgent(
    name="trip_planner",
    model=MODEL,
    instruction="Help plan day trips. Delegate any weather question to weather_agent, then suggest an activity.",
    sub_agents=[remote_weather],
)


if __name__ == "__main__":
    phase("A2A: discover agent card, send task, receive response")
    show("initial prompt", "I'm in Madrid tomorrow. What should I do outdoors?")
    events = asyncio.run(InMemoryRunner(agent=trip_planner).run_debug("I'm in Madrid tomorrow. What should I do outdoors?", quiet=True))
    for event in events:
        phase(f"{event.author}")
        show_event(event)
