from dataclasses import dataclass, field
from typing import Any, Literal, cast

from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI

from step_logger import phase, show

CHEAP_MODEL = "gemini-3.5-flash-lite"
STRONG_MODEL = "gemini-3.1-pro-preview"
ILLUSTRATIVE_USD_PER_MILLION_TOKENS = {CHEAP_MODEL: 0.60, STRONG_MODEL: 5.00}
STRONG_CALL_RESERVE_USD = 0.01

Complexity = Literal["simple", "complex"]


class Triage(BaseModel):
    complexity: Complexity


@dataclass
class Budget:
    limit_usd: float
    spent_usd: float = 0.0
    log: list[str] = field(default_factory=list)

    @property
    def remaining_usd(self) -> float:
        return self.limit_usd - self.spent_usd

    def charge(self, model: str, total_tokens: int) -> None:
        cost = total_tokens / 1_000_000 * ILLUSTRATIVE_USD_PER_MILLION_TOKENS[model]
        self.spent_usd += cost
        self.log.append(f"{model}: {total_tokens} tokens, ${cost:.5f}")


def choose_model(complexity: Complexity, budget: Budget) -> str:
    if complexity == "complex" and budget.remaining_usd >= STRONG_CALL_RESERVE_USD:
        return STRONG_MODEL
    return CHEAP_MODEL


triage = ChatGoogleGenerativeAI(model=CHEAP_MODEL).with_structured_output(Triage, include_raw=True)
models = {name: ChatGoogleGenerativeAI(model=name) for name in (CHEAP_MODEL, STRONG_MODEL)}


def served_model(reply, requested: str) -> str:
    name = reply.response_metadata.get("model_name", "").removeprefix("models/")
    return name if name in ILLUSTRATIVE_USD_PER_MILLION_TOKENS else requested


def answer(question: str, budget: Budget) -> str:
    phase(f"Triage: {question}")
    triaged = cast(dict[str, Any], triage.invoke("Is this question simple factual recall, or complex multi-step reasoning?\n" + question))
    budget.charge(CHEAP_MODEL, triaged["raw"].usage_metadata["total_tokens"])
    complexity = triaged["parsed"].complexity
    show("triage", triaged["parsed"])
    phase("Route: choose model")
    model = choose_model(complexity, budget)
    show("chosen model", {"model": model, "remaining_usd": budget.remaining_usd})
    llm = models[model] if model == CHEAP_MODEL else models[model].with_fallbacks([models[CHEAP_MODEL]])
    reply = llm.invoke(question)
    phase("Cost")
    assert reply.usage_metadata is not None
    budget.charge(served_model(reply, model), reply.usage_metadata["total_tokens"])
    show("charge", {"served": served_model(reply, model), "log": budget.log[-1], "remaining_usd": budget.remaining_usd})
    return f"[{complexity} -> {served_model(reply, model)}] {reply.text}"


if __name__ == "__main__":
    assert choose_model("simple", Budget(1.0)) == CHEAP_MODEL
    assert choose_model("complex", Budget(1.0)) == STRONG_MODEL
    assert choose_model("complex", Budget(1.0, spent_usd=0.995)) == CHEAP_MODEL
    budget = Budget(limit_usd=0.05)
    for question in ["What is the capital of Australia?",
                     "Compare the long-term effects of quantum computing on RSA and lattice-based cryptography."]:
        show("initial prompt", question)
        print(answer(question, budget), "\n")
    print("\n".join(budget.log), f"\nremaining: ${budget.remaining_usd:.4f}")
