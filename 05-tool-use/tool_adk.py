import asyncio
import json
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner

from step_logger import phase, show, show_event

MODEL = "gemini-3.5-flash-lite"

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
REQUEST_TIMEOUT_SECONDS = 10

def fetch_json(url: str, params: dict) -> dict:
    with urlopen(f"{url}?{urlencode(params)}", timeout=REQUEST_TIMEOUT_SECONDS) as response:
        return json.load(response)


def get_weather(city: str) -> dict:
    """Returns current weather for a city: temperature in °C, wind in km/h, WMO weather code."""
    try:
        places = fetch_json(GEOCODING_URL, {"name": city, "count": 1}).get("results", [])
        if not places:
            return {"status": "error", "message": f"No weather data for {city}"}
        place = places[0]
        current = fetch_json(
            FORECAST_URL,
            {
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "current": "temperature_2m,weather_code,wind_speed_10m",
            },
        )["current"]
    except (URLError, TimeoutError, KeyError) as error:
        return {"status": "error", "message": f"Weather service failed: {error}"}
    return {
        "status": "ok",
        "location": f"{place['name']}, {place.get('country', '')}",
        "temperature_c": current["temperature_2m"],
        "wind_kmh": current["wind_speed_10m"],
        "wmo_weather_code": current["weather_code"],
    }


agent = Agent(
    name="WeatherAgent",
    model=MODEL,
    instruction="Answer weather questions using get_weather. If the tool returns an error, just say you don't know the answer.",
    tools=[get_weather],
)


if __name__ == "__main__":
    phase("Tool use: agent calls get_weather")
    show("initial prompt", ["Weather in London?", "Weather in Tokyo?"])
    events = asyncio.run(InMemoryRunner(agent=agent).run_debug(["Weather in London?", "Weather in Tokyo?"], quiet=True))
    for event in events:
        show_event(event)
    phase("Tool use done")
