import uuid
from dataclasses import dataclass
from typing import cast

from langchain_core.messages import HumanMessage

from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.runtime import Runtime
from langgraph.store.memory import InMemoryStore

from step_logger import phase, show

MODEL = "gemini-3.5-flash-lite"


@dataclass
class Context:
    user_id: str


class DurableFacts(BaseModel):
    facts: list[str]


llm = ChatGoogleGenerativeAI(model=MODEL)


def respond(state: MessagesState, runtime: Runtime[Context]) -> dict:
    namespace = ("facts", runtime.context.user_id)
    assert runtime.store is not None
    known = [item.value["fact"] for item in runtime.store.search(namespace)]
    phase(f"Retrieve long-term memory {namespace}")
    show("known facts", known)
    system = f"You are a helpful assistant. Known facts about this user: {known or 'none yet'}"
    return {"messages": [llm.invoke([("system", system), *state["messages"]])]}


def remember(state: MessagesState, runtime: Runtime[Context]) -> dict:
    extracted = cast(
        DurableFacts,
        llm.with_structured_output(DurableFacts).invoke(
            "List durable facts about the user (name, preferences, constraints) stated in this message, "
            f"or an empty list:\n{state['messages'][-2].content}"
        ),
    )
    assert runtime.store is not None
    phase("Write long-term memory")
    show("extracted facts", extracted)
    for fact in extracted.facts:
        runtime.store.put(("facts", runtime.context.user_id), str(uuid.uuid4()), {"fact": fact})
    return {}


builder = StateGraph(MessagesState, context_schema=Context)
builder.add_node(respond)
builder.add_node(remember)
builder.add_edge(START, "respond")
builder.add_edge("respond", "remember")
app = builder.compile(checkpointer=InMemorySaver(), store=InMemoryStore())


def chat(text: str, thread_id: str, user_id: str = "jane") -> str:
    result = app.invoke(
        {"messages": [HumanMessage(text)]},
        {"configurable": {"thread_id": thread_id}},
        context=Context(user_id=user_id),
    )
    return result["messages"][-1].text


if __name__ == "__main__":
    phase("Thread t1: state a fact")
    show("initial prompt", "Hi, I'm Jane and I'm vegetarian.")
    print(chat("Hi, I'm Jane and I'm vegetarian.", thread_id="t1"))
    phase("Thread t1: short-term memory recall")
    show("initial prompt", "What's my name?")
    print(chat("What's my name?", thread_id="t1", user_id="empty-store"))
    phase("Thread t2: new thread, long-term memory recall")
    show("initial prompt", "Suggest a dinner recipe for me.")
    print(chat("Suggest a dinner recipe for me.", thread_id="t2"))
