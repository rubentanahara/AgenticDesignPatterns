import asyncio

from google.adk.agents import LlmAgent
from google.adk.events import Event, EventActions
from google.adk.runners import InMemoryRunner

from step_logger import phase, show, show_event
from google.adk.workflow import START, Workflow
from pydantic import BaseModel

MODEL = "gemini-3.5-flash-lite"
WRITER_MODEL = "gemma-4-26b-a4b-it"
MAX_ROUNDS = 3


class Verdict(BaseModel):
    approved: bool
    issues: list[str]

writer = LlmAgent(
    name="Writer",
    model=WRITER_MODEL,
    instruction=(
        "Write or revise a short, factual paragraph on the user's subject. "
        "If state has a critique, fix every point in it: {critique?}"
    ),
    output_key="draft",
)

fact_checker = LlmAgent(
    name="FactChecker",
    model=MODEL,
    instruction=(
        "Fact-check this paragraph: {draft}\n"
        "Required: all three crew names, the lunar module's name, and the exact UTC landing time. "
        "Report only the single most important inaccurate or missing item per review. "
        "Set approved only if every claim is accurate and nothing required is missing; otherwise list that item in issues."
    ),
    output_schema=Verdict,
    output_key="critique",
)

def gate(ctx, node_input):
    rounds = ctx.state.get("rounds", 0) + 1
    approved = node_input["approved"] if isinstance(node_input, dict) else node_input.approved
    route = "revise" if not approved and rounds < MAX_ROUNDS else None
    return Event(actions=EventActions(route=route, state_delta={"rounds": rounds}))


reflection_loop = Workflow(
    name="WriteAndReview",
    edges=[(START, writer, fact_checker, gate), (gate, {"revise": writer})],
)


if __name__ == "__main__":
    phase("Reflection: write, fact-check, revise loop")
    show("initial prompt", "The Apollo 11 mission")
    events = asyncio.run(InMemoryRunner(node=reflection_loop).run_debug("The Apollo 11 mission", quiet=True))
    for event in events:
        show_event(event)
    phase("Reflection done")
