from dataclasses import dataclass, field

from typing import cast

from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI

from step_logger import phase, show

MODEL = "gemini-3.5-flash-lite"
URGENCY_WEIGHT, IMPORTANCE_WEIGHT, EFFORT_PENALTY = 2.0, 1.5, 0.5


class Assessment(BaseModel):
    urgency: int = Field(ge=1, le=5)
    importance: int = Field(ge=1, le=5)
    effort: int = Field(ge=1, le=5)


@dataclass
class Task:
    id: str
    title: str
    assessment: Assessment
    depends_on: list[str] = field(default_factory=list)

    @property
    def priority(self) -> float:
        a = self.assessment
        return URGENCY_WEIGHT * a.urgency + IMPORTANCE_WEIGHT * a.importance - EFFORT_PENALTY * a.effort


def ranked_ready(backlog: list[Task], done: set[str]) -> list[Task]:
    ready = [task for task in backlog if task.id not in done and set(task.depends_on) <= done]
    return sorted(ready, key=lambda task: task.priority, reverse=True)


assessor = ChatGoogleGenerativeAI(model=MODEL).with_structured_output(Assessment)


def assess(title: str) -> Assessment:
    return cast(Assessment, assessor.invoke(
        "Rate this engineering task from 1 to 5 on urgency (time sensitivity), importance "
        f"(impact on the product), and effort (work required):\n{title}"
    ))


def make_task(task_id: str, title: str, depends_on: list[str] | None = None) -> Task:
    task = Task(task_id, title, assess(title), depends_on or [])
    show(f"{task_id}: {title}", task.assessment)
    return task


if __name__ == "__main__":
    def fixed(u, i, e):
        return Assessment(urgency=u, importance=i, effort=e)

    demo = [Task("T1", "docs", fixed(1, 2, 1)), Task("T2", "schema", fixed(3, 4, 3)),
            Task("T3", "migrate", fixed(5, 5, 2), depends_on=["T2"])]
    assert ranked_ready(demo, set())[0].id == "T2"
    assert ranked_ready(demo, {"T2"})[0].id == "T3"
    assert ranked_ready(demo, {"T1", "T2", "T3"}) == []

    phase("LLM ratings")
    backlog = [
        make_task("T1", "Update the README screenshots"),
        make_task("T2", "Design the new login database schema"),
        make_task("T3", "Implement the new login system", depends_on=["T2"]),
        make_task("T4", "Review marketing website copy"),
    ]
    done: set[str] = set()
    while ready := ranked_ready(backlog, done):
        phase("Ranked order")
        show("ready tasks", [f"{t.id} priority={t.priority:.1f} {t.title}" for t in ready])
        task = ready[0]
        done.add(task.id)
        if task.id == "T2":
            phase("New event: re-rank")
            backlog.append(make_task("T5", "Production checkout is down for all users"))
