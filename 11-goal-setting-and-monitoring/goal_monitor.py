from dataclasses import dataclass
from typing import Callable

from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI

from step_logger import phase, show

MODEL = "gemini-3.5-flash-lite"
MAX_ATTEMPTS = 4
MAX_WORDS = 60


@dataclass
class Goal:
    name: str
    check: Callable[[str], bool]


class ToneVerdict(BaseModel):
    friendly_and_concrete: bool


writer = ChatGoogleGenerativeAI(model=MODEL)
judge = ChatGoogleGenerativeAI(model=MODEL).with_structured_output(ToneVerdict)


def judged_friendly(text: str) -> bool:
    return judge.invoke(f"Is this product copy friendly and concrete (no vague hype)?\n\n{text}").friendly_and_concrete


GOALS = [
    Goal(f"at most {MAX_WORDS} words", lambda text: len(text.split()) <= MAX_WORDS),
    Goal("states the price $49", lambda text: "$49" in text),
    Goal("mentions the 2-year warranty", lambda text: "2-year" in text.lower() or "two-year" in text.lower()),
    Goal("friendly, concrete tone", judged_friendly),
]


def monitor(text: str) -> list[str]:
    return [goal.name for goal in GOALS if not goal.check(text)]


def pursue(brief: str) -> tuple[str, str]:
    goal_list = "\n".join(f"- {goal.name}" for goal in GOALS)
    draft, unmet = "", [goal.name for goal in GOALS]
    for attempt in range(1, MAX_ATTEMPTS + 1):
        phase(f"Attempt {attempt}/{MAX_ATTEMPTS}: write draft")
        feedback = f"\nPrevious draft:\n{draft}\nStill unmet: {unmet}" if draft else ""
        draft = writer.invoke(f"{brief}\nGoals:\n{goal_list}{feedback}\nReturn only the copy.").text.strip()
        show("draft", draft)
        phase(f"Attempt {attempt}: monitor goals")
        unmet = []
        for goal in GOALS:
            passed = goal.check(draft)
            show(goal.name, "pass" if passed else "fail", "green" if passed else "red")
            if not passed:
                unmet.append(goal.name)
        if not unmet:
            phase("Goals achieved")
            return "achieved", draft
    phase("Escalate to human")
    return f"escalate to human, unmet after {MAX_ATTEMPTS} attempts: {unmet}", draft


if __name__ == "__main__":
    assert GOALS[0].check("short text") and not GOALS[0].check("word " * (MAX_WORDS + 1))
    assert GOALS[1].check("Only $49!") and not GOALS[1].check("Only $59!")
    show("initial prompt", "Write product copy for the TrailLite headlamp: 400 lumens, USB-C, $49, 2-year warranty.")
    status, copy = pursue("Write product copy for the TrailLite headlamp: 400 lumens, USB-C, $49, 2-year warranty.")
    print(status, "\n", copy)
