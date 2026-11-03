import subprocess
import sys
from pathlib import Path

from langchain_google_genai import ChatGoogleGenerativeAI

from step_logger import phase, show

MODEL = "gemini-3.1-pro-preview"
PROMPTS = Path(__file__).with_name("prompts")
BRIEF_FILE = Path("task-context/BRIEF.md")
NO_BRIEF = "No brief provided."


def staged_diff() -> str:
    return subprocess.run(["git", "diff", "--cached"], capture_output=True, text=True, check=True).stdout


def load_brief(path: Path = BRIEF_FILE) -> str:
    return path.read_text() if path.exists() else NO_BRIEF


def render(prompt_name: str, **values: str) -> str:
    return (PROMPTS / f"{prompt_name}.md").read_text().format(**values)


def review(diff: str, brief: str) -> str:
    llm = ChatGoogleGenerativeAI(model=MODEL)
    phase("Critique staged diff")
    critique = llm.invoke(render("critique", brief=brief, diff=diff)).text
    show("critique", critique)
    phase("Reflect on critique")
    return llm.invoke(render("reflect", critique=critique)).text


if __name__ == "__main__":
    assert "<diff>\nx\n</diff>" in render("critique", brief="b", diff="x")
    assert load_brief(Path("does-not-exist.md")) == NO_BRIEF
    phase("Collect staged diff")
    diff = staged_diff()
    if not diff.strip():
        sys.exit("Nothing staged to review.")
    result = review(diff, load_brief())
    phase("Review result")
    print(result)
