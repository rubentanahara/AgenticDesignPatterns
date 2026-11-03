import itertools
from typing import Literal, cast

from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI

from step_logger import phase, show

MODEL = "gemini-3.5-flash-lite"
HYPOTHESES = 4
INITIAL_ELO = 1200.0
ELO_K = 32

RESEARCH_GOAL = "Why do some open-source projects keep contributors for years while most lose them within months?"


class Hypotheses(BaseModel):
    items: list[str]


class Match(BaseModel):
    winner: Literal["A", "B"]
    reason: str


creative = ChatGoogleGenerativeAI(model=MODEL)
judge = ChatGoogleGenerativeAI(model=MODEL).with_structured_output(Match)


def elo_update(winner: float, loser: float) -> tuple[float, float]:
    expected_win = 1 / (1 + 10 ** ((loser - winner) / 400))
    delta = ELO_K * (1 - expected_win)
    return winner + delta, loser - delta


def generate(goal: str) -> list[str]:
    return cast(Hypotheses, creative.with_structured_output(Hypotheses).invoke(
        f"Propose {HYPOTHESES} distinct, testable, non-obvious hypotheses for: {goal}"
    )).items


def debate(goal: str, a: str, b: str) -> Match:
    return cast(Match, judge.invoke(
        f"Research goal: {goal}\nAs a critical peer reviewer, pick the hypothesis that is more novel, "
        f"plausible and testable.\nA: {a}\nB: {b}"
    ))


def tournament(goal: str, hypotheses: list[str]) -> dict[str, float]:
    ratings = {h: INITIAL_ELO for h in hypotheses}
    for a, b in itertools.combinations(hypotheses, 2):
        phase("Pairwise debate")
        match = debate(goal, a, b)
        show(f"A: {a}\nB: {b}", match)
        winner, loser = (a, b) if match.winner == "A" else (b, a)
        ratings[winner], ratings[loser] = elo_update(ratings[winner], ratings[loser])
        show("Elo update", {winner: ratings[winner], loser: ratings[loser]})
    return ratings


def evolve(goal: str, best: str) -> str:
    return creative.invoke(
        f"Research goal: {goal}\nTop hypothesis: {best}\n"
        "Refine it: make it sharper, combine it with an unconventional angle, and add one concrete experiment "
        "that could falsify it. Answer in under 120 words."
    ).text


if __name__ == "__main__":
    up, down = elo_update(1200, 1200)
    assert (round(up), round(down)) == (1216, 1184)
    phase("Generate hypotheses")
    show("initial prompt", RESEARCH_GOAL)
    hypotheses = generate(RESEARCH_GOAL)
    show("hypotheses", hypotheses)
    ratings = tournament(RESEARCH_GOAL, hypotheses)
    phase("Final ratings")
    for hypothesis, rating in sorted(ratings.items(), key=lambda item: -item[1]):
        print(f"{rating:7.1f}  {hypothesis}")
    phase("Evolve top hypothesis")
    print(evolve(RESEARCH_GOAL, max(ratings, key=lambda hypothesis: ratings[hypothesis])))
