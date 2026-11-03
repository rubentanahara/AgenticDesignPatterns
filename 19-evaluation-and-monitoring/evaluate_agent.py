import asyncio
import json
import time

from google import genai
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from typing import cast

from pydantic import BaseModel

from step_logger import phase, show, show_event
from trajectory_metrics import score

MODEL = "gemini-3.5-flash-lite"
JUDGE_MODEL = "gemini-3.5-flash-lite"

DEVICES = {("bedroom", "device_2"): "ON"}


def get_device_info(location: str, device_id: str) -> dict:
    """Returns the current status of a smart-home device."""
    return {"status": DEVICES.get((location.lower(), device_id), "UNKNOWN")}


def set_device_info(location: str, device_id: str, status: str) -> dict:
    """Sets a smart-home device ON or OFF."""
    DEVICES[(location.lower(), device_id)] = status.upper()
    return {"result": f"{device_id} in {location} set to {status.upper()}"}


home_agent = Agent(
    name="HomeAgent",
    model=MODEL,
    instruction="Control smart-home devices with the tools. Confirm what you did in one sentence.",
    tools=[get_device_info, set_device_info],
)

EVAL_SET = [
    {"query": "Turn off device_2 in the Bedroom.", "expected_tools": ["set_device_info"]},
    {"query": "Is device_2 in the bedroom on? If it is, switch it off.",
     "expected_tools": ["get_device_info", "set_device_info"]},
]

RUBRIC = """Rate the assistant's reply for helpfulness from 1 to 5:
5 = fully answers, accurate, concise; 3 = partially helpful; 1 = unhelpful or wrong."""


class Judgement(BaseModel):
    helpfulness: int
    rationale: str


judge = genai.Client()


def judge_helpfulness(query: str, reply: str) -> Judgement:
    return cast(Judgement, judge.models.generate_content(
        model=JUDGE_MODEL,
        contents=f"{RUBRIC}\n\nUser: {query}\nAssistant: {reply}",
        config={"response_mime_type": "application/json", "response_schema": Judgement},
    ).parsed)


async def run_case(runner: InMemoryRunner, case_id: int, query: str) -> dict:
    started = time.perf_counter()
    events = await runner.run_debug(query, session_id=f"eval-{case_id}", quiet=True)
    for event in events:
        show_event(event)
    tools = [call.name for event in events for call in event.get_function_calls()]
    tokens = sum(event.usage_metadata.total_token_count or 0 for event in events if event.usage_metadata)
    reply = next((e.content.parts[0].text for e in reversed(events) if e.is_final_response() and e.content and e.content.parts), "")
    return {"tools": tools, "reply": reply, "latency_s": round(time.perf_counter() - started, 2), "tokens": tokens}


async def main() -> None:
    runner = InMemoryRunner(agent=home_agent)
    for case_id, case in enumerate(EVAL_SET):
        DEVICES[("bedroom", "device_2")] = "ON"
        phase(f"Case {case_id}: run agent")
        show("initial prompt", case["query"])
        run = await run_case(runner, case_id, case["query"])
        phase(f"Case {case_id}: trajectory score")
        trajectory = score(run["tools"], case["expected_tools"])
        show("trajectory", trajectory)
        phase(f"Case {case_id}: judge score")
        judgement = judge_helpfulness(case["query"], run["reply"])
        show("judgement", judgement)
        report = {
            "query": case["query"],
            "trajectory": trajectory,
            "helpfulness": judgement.helpfulness,
            "latency_s": run["latency_s"],
            "tokens": run["tokens"],
        }
        print(json.dumps(report))


if __name__ == "__main__":
    asyncio.run(main())
