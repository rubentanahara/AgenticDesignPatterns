from langchain_core.runnables import RunnableLambda
from langchain_google_genai import ChatGoogleGenerativeAI

from step_logger import phase, show

PRIMARY_MODEL = "gemini-3.1-pro-preview"
BACKUP_MODEL = "gemini-3.5-flash-lite"


class TransientError(Exception):
    pass


class NotFoundError(Exception):
    pass


GEOCODER_OUTAGES = {"remaining": 2}
KNOWN_ADDRESSES = {"1600 amphitheatre pkwy, mountain view": "37.422, -122.084"}


def precise_location(address: str) -> str:
    if GEOCODER_OUTAGES["remaining"] > 0:
        GEOCODER_OUTAGES["remaining"] -= 1
        phase("Attempt: precise lookup")
        show("error", "geocoder timeout, will retry", "red")
        raise TransientError("geocoder timeout")
    if address.lower() not in KNOWN_ADDRESSES:
        phase("Attempt: precise lookup")
        show("error", f"precise lookup failed for {address!r}, falling back", "red")
        raise NotFoundError(address)
    show("precise lookup", "success")
    return f"precise: {KNOWN_ADDRESSES[address.lower()]}"


def general_area(address: str) -> str:
    phase("Fallback: general area")
    city = address.split(",")[-1].strip()
    return f"approximate: city of {city.title()}"


locate = (
    RunnableLambda(precise_location)
    .with_retry(retry_if_exception_type=(TransientError,), stop_after_attempt=3, wait_exponential_jitter=False)
    .with_fallbacks([RunnableLambda(general_area)])
)

llm = ChatGoogleGenerativeAI(model=PRIMARY_MODEL).with_fallbacks([ChatGoogleGenerativeAI(model=BACKUP_MODEL)])


def answer(address: str) -> str:
    try:
        location = locate.invoke(address)
    except Exception:
        phase("Degraded: escalating to support")
        show("error", "all location strategies failed", "red")
        return "Sorry, I couldn't find that location. A support agent will follow up."
    phase("Generate answer")
    show("location", location)
    return llm.invoke(f"Tell the user where {address!r} is, using only this data: {location}").text


if __name__ == "__main__":
    assert locate.invoke("1600 Amphitheatre Pkwy, Mountain View").startswith("precise")
    assert locate.invoke("12 Unknown St, Springfield") == "approximate: city of Springfield"
    show("initial prompt", "12 Unknown St, Springfield")
    print(answer("12 Unknown St, Springfield"))
