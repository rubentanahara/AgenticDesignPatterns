import asyncio

from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from google.adk.tools import AgentTool

from step_logger import phase, show, show_event

MODEL = "gemini-3.5-flash-lite"

researcher = LlmAgent(
    name="Researcher",
    model=MODEL,
    description="Finds the 3 most important facts about a topic.",
    instruction="Return exactly 3 short, factual bullet points about the requested topic.",
)

writer = LlmAgent(
    name="Writer",
    model=MODEL,
    description="Turns bullet-point facts into a short, engaging blog paragraph.",
    instruction="Write one engaging paragraph using only the facts you are given.",
)

editor = LlmAgent(
    name="Editor",
    model=MODEL,
    description="Checks a paragraph against its source facts and fixes unsupported claims.",
    instruction="Compare the paragraph with the facts. Remove or fix anything not supported. Return the final text.",
)

supervisor = LlmAgent(
    name="Supervisor",
    model=MODEL,
    instruction=(
        "You run a small content team. For the user's topic: call Researcher, pass its facts to Writer, "
        "then pass both the facts and the paragraph to Editor. Reply with the Editor's final text only."
    ),
    tools=[AgentTool(agent=researcher), AgentTool(agent=writer), AgentTool(agent=editor)],
)


async def main() -> None:
    phase("Supervisor delegates to Researcher, Writer, Editor")
    show("initial prompt", "AI agents in 2025")
    events = await InMemoryRunner(agent=supervisor).run_debug("AI agents in 2025", quiet=True)
    for event in events:
        show_event(event)
    phase("Team finished")


if __name__ == "__main__":
    asyncio.run(main())
