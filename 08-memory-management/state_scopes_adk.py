import asyncio
import time

from google.adk.events import Event, EventActions
from google.adk.sessions import InMemorySessionService, Session

from step_logger import phase, show

APP, USER = "memory_demo", "jane"


async def load_session(sessions: InMemorySessionService, session_id: str) -> Session:
    session = await sessions.get_session(app_name=APP, user_id=USER, session_id=session_id)
    if session is None:
        raise LookupError(f"session {session_id} not found")
    return session


async def record_login(sessions: InMemorySessionService, session_id: str) -> None:
    session = await load_session(sessions, session_id)
    delta = {
        "user:login_count": session.state.get("user:login_count", 0) + 1,
        "task_status": "active",
        "temp:validation_needed": True,
    }
    event = Event(author="system", invocation_id=f"login-{time.time()}", actions=EventActions(state_delta=delta))
    show(f"{session_id} state_delta", delta, "yellow")
    await sessions.append_event(session, event)


async def main() -> None:
    sessions = InMemorySessionService()
    for session_id in ("chat-1", "chat-2"):
        phase(f"Session {session_id}: write session, user and temp scopes")
        await sessions.create_session(app_name=APP, user_id=USER, session_id=session_id)
        await record_login(sessions, session_id)

    first = await load_session(sessions, "chat-1")
    second = await load_session(sessions, "chat-2")
    phase("Read back: user: persists across sessions, temp: is dropped")
    show("chat-1 state", dict(first.state))
    show("chat-2 state", dict(second.state))

    assert second.state["user:login_count"] == 2
    assert "temp:validation_needed" not in second.state


if __name__ == "__main__":
    asyncio.run(main())
