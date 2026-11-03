from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, ToolCall, ToolMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

from step_logger import phase, show

MODEL = "gemini-3.5-flash-lite"
MAX_STEPS = 10

PRICES = {"AAPL": 178.15, "GOOGL": 1750.30, "MSFT": 425.50}

SYSTEM_PROMPT = (
    "You solve tasks with the ReAct loop. Before every tool call, write one line starting with "
    "'Thought:' that says what you know and what you need next. Then call exactly one tool. "
    "After you see the Observation, think again. When you have enough information, write "
    "'Thought:' followed by your reasoning, then 'Final Answer:' followed by the answer, and call no tool."
)


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


@tool
def add(a: float, b: float) -> float:
    """Adds two numbers exactly."""
    return a + b


TOOLS = {t.name: t for t in (get_stock_price, multiply, add)}
llm = ChatGoogleGenerativeAI(model=MODEL).bind_tools(list(TOOLS.values()))


def observe(call: ToolCall) -> ToolMessage:
    show(f"Action: {call['name']}", call["args"], "yellow")
    try:
        result = TOOLS[call["name"]].invoke(call["args"])
    except Exception as error:
        result = f"ERROR: {error}"
    show("Observation", result, "magenta")
    return ToolMessage(content=str(result), tool_call_id=call["id"])


def react(question: str) -> str:
    messages: list[BaseMessage] = [SystemMessage(SYSTEM_PROMPT), HumanMessage(question)]
    for step in range(1, MAX_STEPS + 1):
        phase(f"Step {step}")
        reply = llm.invoke(messages)
        if not reply.tool_calls and not reply.text:
            continue
        messages.append(reply)
        if reply.text:
            show("Thought", reply.text, "cyan")
        if not reply.tool_calls:
            return reply.text
        messages += [observe(call) for call in reply.tool_calls]
    raise RuntimeError("Agent did not finish within MAX_STEPS")


if __name__ == "__main__":
    assert observe({"name": "multiply", "args": {"a": 2, "b": 3}, "id": "1"}).content == "6.0"
    assert observe({"name": "get_stock_price", "args": {"ticker": "XYZ"}, "id": "2"}).text.startswith("ERROR")
    show("initial prompt", "What would 100 shares of AAPL plus 10 shares of MSFT cost right now?")
    print(react("What would 100 shares of AAPL plus 10 shares of MSFT cost right now?"))
