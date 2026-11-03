import operator
from typing import Annotated, TypedDict

from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph

from step_logger import phase, show

MODEL = "gemini-3.5-flash-lite"
MAX_STEPS = 6


class Plan(BaseModel):
    steps: list[str]


class Replan(BaseModel):
    done: bool
    final_answer: str
    remaining_steps: list[str]


class State(TypedDict):
    goal: str
    plan: list[str]
    completed: Annotated[list[tuple[str, str]], operator.add]
    answer: str


llm = ChatGoogleGenerativeAI(model=MODEL)


def plan(state: State) -> dict:
    phase("Plan")
    result = llm.with_structured_output(Plan).invoke(
        f"Break this goal into 2-4 concrete, ordered steps:\n{state['goal']}"
    )
    show("plan", result)
    return {"plan": result.steps}


def execute(state: State) -> dict:
    step = state["plan"][0]
    phase(f"Execute: {step}")
    output = llm.invoke(f"Goal: {state['goal']}\nDone so far: {state['completed']}\nNow do this step: {step}")
    show("step result", output.text)
    return {"completed": [(step, output.text)], "plan": state["plan"][1:]}


def replan(state: State) -> dict:
    phase("Replan")
    result = llm.with_structured_output(Replan).invoke(
        f"Goal: {state['goal']}\nCompleted steps and results: {state['completed']}\n"
        f"Remaining plan: {state['plan']}\n"
        "If the goal is met, set done=true and write final_answer. "
        "Otherwise return the remaining steps, changed if the results call for it."
    )
    show("replan", result)
    if result.done or len(state["completed"]) >= MAX_STEPS:
        return {"answer": result.final_answer or state["completed"][-1][1], "plan": []}
    return {"plan": result.remaining_steps}


def next_node(state: State) -> str:
    return "execute" if state["plan"] else END


graph = StateGraph(State)
graph.add_node("plan", plan)
graph.add_node("execute", execute)
graph.add_node("replan", replan)
graph.add_edge(START, "plan")
graph.add_edge("plan", "execute")
graph.add_edge("execute", "replan")
graph.add_conditional_edges("replan", next_node, ["execute", END])
app = graph.compile()


if __name__ == "__main__":
    show("initial prompt", "Write a 150-word summary on why reinforcement learning matters in AI.")
    result = app.invoke({"goal": "Write a 150-word summary on why reinforcement learning matters in AI."})
    phase("Final answer")
    for step, _ in result["completed"]:
        print("step:", step)
    print("\n" + result["answer"])
