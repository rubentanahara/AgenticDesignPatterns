import asyncio

from google.adk.agents import Agent
from google.adk.code_executors import BuiltInCodeExecutor
from google.adk.runners import InMemoryRunner

from step_logger import phase, show, show_event

MODEL = "gemini-3.5-flash-lite"

calculator = Agent(
    name="ProgramAidedSolver",
    model=MODEL,
    instruction=(
        "Never do arithmetic in your head. Write Python code that computes the answer, run it, "
        "and report the result in one sentence."
    ),
    code_executor=BuiltInCodeExecutor(),
)


if __name__ == "__main__":
    phase("Program-aided reasoning: write code, execute, report")
    show("initial prompt", "What is the sum of all primes below 10,000, and how many of them end in 7?")
    events = asyncio.run(InMemoryRunner(agent=calculator).run_debug(
        "What is the sum of all primes below 10,000, and how many of them end in 7?", quiet=True
    ))
    for event in events:
        show_event(event)
