from typing import Literal, TypedDict, cast

from pydantic import BaseModel
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from step_logger import phase, show

MODEL = "gemini-3.5-flash-lite"
AUTO_APPROVE_LIMIT_USD = 50


class RefundRequest(BaseModel):
    amount_usd: float
    reason: str


class State(TypedDict):
    message: str
    request: dict
    decision: Literal["approved", "rejected"]
    approved_by: str
    outcome: str


llm = ChatGoogleGenerativeAI(model=MODEL)


def extract(state: State) -> dict:
    phase("Extract refund request")
    request = cast(RefundRequest, llm.with_structured_output(RefundRequest).invoke(state["message"]))
    show("request", request)
    return {"request": request.model_dump()}


def gate(state: State) -> dict:
    request = state["request"]
    phase("Gate decision")
    if request["amount_usd"] <= AUTO_APPROVE_LIMIT_USD:
        show("gate", f"auto-approved, at most ${AUTO_APPROVE_LIMIT_USD}")
        return {"decision": "approved", "approved_by": "policy"}
    show("gate", f"above ${AUTO_APPROVE_LIMIT_USD}, interrupting for human", "yellow")
    answer = interrupt({"question": "Approve this refund?", "amount_usd": request["amount_usd"], "reason": request["reason"]})
    return {"decision": "approved" if answer == "yes" else "rejected", "approved_by": "human"}


def execute(state: State) -> dict:
    phase("Execute")
    show("decision", f"{state['decision']} by {state['approved_by']}")
    if state["decision"] == "rejected":
        return {"outcome": "Refund declined. A specialist will contact the customer."}
    return {"outcome": f"Refunded ${state['request']['amount_usd']:.2f} (approved by {state['approved_by']})."}


graph = StateGraph(State)
graph.add_node("extract", extract)
graph.add_node("gate", gate)
graph.add_node("execute", execute)
graph.add_edge(START, "extract")
graph.add_edge("extract", "gate")
graph.add_edge("gate", "execute")
graph.add_edge("execute", END)
app = graph.compile(checkpointer=InMemorySaver())


def handle(message: str, thread_id: str) -> str:
    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
    result = app.invoke(cast(State, {"message": message}), config)
    while "__interrupt__" in result:
        phase("Interrupt: human review")
        show("HUMAN REVIEW", result["__interrupt__"][0].value, "yellow")
        result = app.invoke(Command(resume=input("yes/no> ").strip().lower()), config)
    return result["outcome"]


if __name__ == "__main__":
    show("initial prompt", "My $20 charger arrived broken, please refund it.")
    print(handle("My $20 charger arrived broken, please refund it.", thread_id="small"))
    show("initial prompt", "Refund my $900 laptop, I changed my mind after 3 months.")
    print(handle("Refund my $900 laptop, I changed my mind after 3 months.", thread_id="large"))
