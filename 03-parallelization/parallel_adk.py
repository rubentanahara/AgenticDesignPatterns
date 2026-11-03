import asyncio

from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from google.adk.workflow import START, JoinNode, Workflow

from step_logger import phase, show, show_event

MODEL = "gemini-3.5-flash-lite"


def researcher(name: str, topic: str) -> LlmAgent:
    return LlmAgent(
        name=name,
        model=MODEL,
        instruction=f"Summarize the latest developments in {topic} in two sentences. Output only the summary.",
        output_key=name,
    )


renewables = researcher("renewables", "renewable energy")
evs = researcher("evs", "electric vehicles")
carbon_capture = researcher("carbon_capture", "carbon capture")

merger = LlmAgent(
    name="Synthesizer",
    model=MODEL,
    instruction=(
        "Write a short report with one heading per topic, using ONLY these findings:\n"
        "Renewables: {renewables}\nEVs: {evs}\nCarbon capture: {carbon_capture}"
    ),
)

pipeline = Workflow(
    name="ResearchThenSynthesize",
    edges=[(START, (renewables, evs, carbon_capture), JoinNode(name="Join"), merger)],
)


if __name__ == "__main__":
    phase("Parallelization: fan-out research, then fan-in synthesis")
    show("initial prompt", "Produce the sustainability report.")
    events = asyncio.run(InMemoryRunner(node=pipeline).run_debug("Produce the sustainability report.", quiet=True))
    for event in events:
        show_event(event)
    phase("Parallelization done")
