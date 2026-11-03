import asyncio
from collections import Counter
from typing import cast

from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI

from step_logger import phase, show

MODEL = "gemini-3.5-flash-lite"
SAMPLES = 5

QUESTION = (
    "A bat and a ball cost $1.10 in total. The bat costs $1.00 more than the ball. "
    "How much does the ball cost, in cents?"
)


class Solution(BaseModel):
    reasoning_steps: list[str]
    final_answer: str


sampler = ChatGoogleGenerativeAI(model=MODEL).with_structured_output(Solution)


def majority(answers: list[str]) -> tuple[str, float]:
    winner, votes = Counter(answer.strip().lower() for answer in answers).most_common(1)[0]
    return winner, votes / len(answers)


async def self_consistent_answer(question: str) -> tuple[str, float]:
    prompt = f"Think step by step, listing each reasoning step, then give only the final answer.\n\n{question}"
    phase(f"Sampling {SAMPLES} independent reasoning paths")
    solutions = await asyncio.gather(*(sampler.ainvoke(prompt) for _ in range(SAMPLES)))
    for index, solution in enumerate(solutions, 1):
        show(f"sample {index}", solution)
    phase("Majority vote")
    return majority([cast(Solution, solution).final_answer for solution in solutions])


if __name__ == "__main__":
    assert majority(["5", "5 ", "10", "5", "10"]) == ("5", 0.6)
    show("initial prompt", QUESTION)
    answer, agreement = asyncio.run(self_consistent_answer(QUESTION))
    print(f"\nmajority answer: {answer} (agreement {agreement:.0%})")
