from langchain_google_genai import ChatGoogleGenerativeAI

from step_logger import phase, show

MODEL = "gemini-3.5-flash-lite"
GENERATIONS = 3

LABELED_TICKETS = [
    ("I was charged twice this month", "billing"),
    ("The app crashes when I upload a photo", "bug"),
    ("Can you add dark mode?", "feature"),
    ("Refund my last invoice please", "billing"),
    ("Export to CSV gives an empty file", "bug"),
    ("It would be great to have a calendar view", "feature"),
]

worker = ChatGoogleGenerativeAI(model=MODEL)
proposer = ChatGoogleGenerativeAI(model=MODEL)


def evaluate(instruction: str) -> tuple[float, list[str]]:
    failures = []
    for ticket, label in LABELED_TICKETS:
        answer = worker.invoke(f"{instruction}\n\nTicket: {ticket}").text.strip().lower()
        if answer != label:
            failures.append(f"{ticket!r}: expected {label}, got {answer!r}")
    return 1 - len(failures) / len(LABELED_TICKETS), failures


def propose(instruction: str, failures: list[str]) -> str:
    return proposer.invoke(
        "Improve this classification instruction so a model answers with exactly one word: "
        "billing, bug, or feature.\n"
        f"Current instruction:\n{instruction}\n\nFailures:\n" + "\n".join(failures) +
        "\n\nReturn only the new instruction."
    ).text.strip()


def evolve(seed: str) -> tuple[float, str]:
    phase("Evaluate seed")
    score, failures = evaluate(seed)
    show("seed", {"instruction": seed, "score": score, "failures": failures})
    archive = [(score, seed, failures)]
    for generation in range(GENERATIONS):
        best_score, best, best_failures = max(archive, key=lambda entry: entry[0])
        phase(f"Generation {generation}: best score {best_score:.2f}")
        if not best_failures:
            break
        candidate = propose(best, best_failures)
        show("proposed instruction", candidate)
        candidate_score, candidate_failures = evaluate(candidate)
        show("evaluated candidate", {"score": candidate_score, "kept": candidate_score > best_score, "failures": candidate_failures})
        archive.append((candidate_score, candidate, candidate_failures))
    best_score, best, _ = max(archive, key=lambda entry: entry[0])
    return best_score, best


if __name__ == "__main__":
    show("initial prompt", "Classify the ticket.")
    result = evolve("Classify the ticket.")
    phase("Best instruction")
    print(result)
