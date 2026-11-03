import uvicorn
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents import LlmAgent

MODEL = "gemini-3.5-flash-lite"
PORT = 8001

FORECASTS = {"london": "rain, 14°C", "madrid": "sunny, 29°C", "tokyo": "humid, 26°C"}


def get_forecast(city: str) -> dict:
    """Returns tomorrow's forecast for a city."""
    if city.lower() not in FORECASTS:
        return {"status": "error", "message": f"No forecast for {city}"}
    return {"status": "ok", "forecast": FORECASTS[city.lower()]}


weather_agent = LlmAgent(
    name="weather_agent",
    model=MODEL,
    description="Provides tomorrow's weather forecast for a city.",
    instruction="Answer forecast questions with get_forecast. Be brief.",
    tools=[get_forecast],
)

app = to_a2a(weather_agent, port=PORT)


if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=PORT)
