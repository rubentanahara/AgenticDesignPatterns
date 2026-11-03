import re
import subprocess
import sys
from typing import cast
from rich.syntax import Syntax
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from step_logger import console, phase, show

MODEL = "gemini-3.5-flash-lite"
PRODUCER_MODEL = "gemma-4-26b-a4b-it"
MAX_ROUNDS = 3

TASK = (
    "Write a Python function calculate_factorial(n). Return 1 for n == 0 "
    "and raise ValueError for negative n. Output only the code."
)


class Critique(BaseModel):
    approved: bool
    issues: list[str]


producer = ChatGoogleGenerativeAI(model=PRODUCER_MODEL)
critic = ChatGoogleGenerativeAI(model=MODEL).with_structured_output(Critique)

CRITIC_PERSONA = SystemMessage(
    "You are a senior Python reviewer. Check the code strictly against the task: bugs, "
    "missing edge cases, style. Required: type hints, a docstring with an example, and an "
    "iterative loop instead of recursion, the error message in a module-level constant, and an "
    "if __name__ == '__main__' demo. Report only the single most important missing item "
    "per review. Approve only if nothing needs to change."
)


def reflect(task: str) -> str:
    history = [HumanMessage(task)]
    phase("Initial draft")
    draft = producer.invoke(history)
    show("draft", draft.text)
    for round_number in range(1, MAX_ROUNDS + 1):
        phase(f"Round {round_number}: critique")
        review = cast(Critique, critic.invoke([CRITIC_PERSONA, HumanMessage(f"Task:\n{task}\n\nCode:\n{draft.text}")]))
        show("critique verdict", review)
        if review.approved:
            break
        phase(f"Round {round_number}: revise")
        history += [draft, HumanMessage("Revise the code to fix these issues:\n- " + "\n- ".join(review.issues))]
        draft = producer.invoke(history)
        show("revised draft", draft.text)
    phase("Final code")
    return draft.text


def run_ruff(command: str, source: str, *options: str) -> subprocess.CompletedProcess[str]:
    arguments = [sys.executable, "-m", "ruff", command, "--stdin-filename", "final.py", *options, "-"]
    return subprocess.run(arguments, input=source, capture_output=True, text=True)


def polish(code: str) -> None:
    source = re.sub(r"^```\w*\n|```\s*$", "", code.strip(), flags=re.MULTILINE)
    phase("Format, lint, highlight")
    formatted = run_ruff("format", source)
    if formatted.returncode == 0:
        source = formatted.stdout
    findings = run_ruff("check", source, "--output-format", "concise", "--quiet")
    show("lint", findings.stdout.strip() or "clean")
    console.print(Syntax(source, "python", theme="monokai", line_numbers=True))


if __name__ == "__main__":
    show("initial prompt", TASK)
    polish(reflect(TASK))
