from langchain_core.messages import BaseMessage, HumanMessage, ToolCall, ToolMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

from step_logger import phase, show

MODEL = "gemini-3.5-flash-lite"
MAX_STEPS = 5

PRICES = {"AAPL": 178.15, "GOOGL": 1750.30, "MSFT": 425.50}


@tool
def get_stock_price(ticker: str) -> float:
    """Returns the latest price in USD for a stock ticker such as AAPL."""
    if ticker.upper() not in PRICES:
        raise ValueError(f"Unknown ticker {ticker!r}")
    return PRICES[ticker.upper()]


@tool
def multiply(a: float, b: float) -> float:
    """Multiplies two numbers exactly."""
    return a * b


TOOLS = {t.name: t for t in (get_stock_price, multiply)}
llm = ChatGoogleGenerativeAI(model=MODEL).bind_tools(list(TOOLS.values()))


def run_tool(call: ToolCall) -> ToolMessage:
    show(f"tool call: {call['name']}", call["args"], "yellow")
    try:
        result = TOOLS[call["name"]].invoke(call["args"])
    except Exception as error:
        result = f"ERROR: {error}"
    show(f"tool result: {call['name']}", result, "magenta")
    return ToolMessage(content=str(result), tool_call_id=call["id"])


def ask(question: str) -> str:
    messages: list[BaseMessage] = [HumanMessage(question)]
    for step in range(1, MAX_STEPS + 1):
        phase(f"Step {step}: model decides")
        reply = llm.invoke(messages)
        messages.append(reply)
        if not reply.tool_calls:
            show("final answer", reply.text)
            return reply.text
        phase(f"Step {step}: run tools")
        messages += [run_tool(call) for call in reply.tool_calls]
    raise RuntimeError("Agent did not finish within MAX_STEPS")


if __name__ == "__main__":
    assert run_tool({"name": "multiply", "args": {"a": 2, "b": 3}, "id": "1"}).content == "6.0"
    assert run_tool({"name": "get_stock_price", "args": {"ticker": "XYZ"}, "id": "2"}).text.startswith("ERROR")
    show("initial prompt", "What would 100 shares of AAPL cost right now?")
    print(ask("What would 100 shares of AAPL cost right now?"))
    show("initial prompt", "What is the price of XYZ?")
    print(ask("What is the price of XYZ?"))
