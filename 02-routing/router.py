from typing import Literal, cast

from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from step_logger import phase, show

MODEL = "gemini-3.5-flash-lite"

Route = Literal["booking", "info", "unclear"]


class RouteDecision(BaseModel):
    route: Route


def handle_booking(request: str) -> str:
    return f"[booking agent] Simulated booking for: {request}"


def handle_info(request: str) -> str:
    return f"[info agent] Simulated lookup for: {request}"


def handle_unclear(request: str) -> str:
    return f"[clarifier] Could you say more about what you need? ({request})"


HANDLERS = {"booking": handle_booking, "info": handle_info, "unclear": handle_unclear}

classify = ChatPromptTemplate.from_messages([
    ("system", "Classify the request. 'booking' for flights or hotels, 'info' for general "
               "questions, 'unclear' if it fits neither."),
    ("user", "{request}"),
]) | ChatGoogleGenerativeAI(model=MODEL).with_structured_output(RouteDecision)


def route_by_rule(request: str) -> Route | None:
    if any(word in request.lower() for word in ("book", "flight", "hotel")):
        return "booking"
    return None


def coordinator(request: str) -> str:
    phase("Classify")
    show("request", request)
    rule_route = route_by_rule(request)
    show("rule-based route", rule_route)
    route = rule_route or cast(RouteDecision, classify.invoke({"request": request})).route
    phase("Chosen route")
    show("route", route)
    phase("Handler")
    return HANDLERS[route](request)


if __name__ == "__main__":
    assert route_by_rule("Book me a hotel in Paris") == "booking"
    assert route_by_rule("What is the capital of Italy?") is None
    for request in ["Book me a flight to London.", "What is the capital of Italy?", "Do the thing."]:
        show("initial prompt", request)
        print(coordinator(request))
