from pydantic import BaseModel, ValidationError
from langchain_google_genai import ChatGoogleGenerativeAI

from step_logger import phase, show

MODEL = "gemini-3.5-flash-lite"

FEW_SHOT_SENTIMENT = """Classify the sentiment of the review as POSITIVE, NEUTRAL, or NEGATIVE.

<examples>
Review: "I found the plot confusing and the characters unlikable." Sentiment: NEGATIVE
Review: "The acting was superb and the story was engaging." Sentiment: POSITIVE
Review: "It was okay, nothing special." Sentiment: NEUTRAL
Review: "Two hours I will never get back." Sentiment: NEGATIVE
Review: "A warm, funny film for the whole family." Sentiment: POSITIVE
</examples>

<review>{review}</review>
Sentiment:"""


class Contact(BaseModel):
    name: str
    address: str
    phone_number: str


llm = ChatGoogleGenerativeAI(model=MODEL)


def few_shot_sentiment(review: str) -> str:
    prompt = FEW_SHOT_SENTIMENT.format(review=review)
    show("few-shot prompt", prompt, "yellow")
    return llm.invoke(prompt).text.strip()


def step_back(task: str, principle_question: str) -> str:
    principles = llm.invoke(principle_question).text
    show("step-back principles", principles)
    prompt = f"<principles>\n{principles}\n</principles>\n\nUsing these principles: {task}"
    show("step-back prompt", prompt, "yellow")
    return llm.invoke(prompt).text


def parse_contact(llm_json: str) -> Contact:
    return Contact.model_validate_json(llm_json)


def extract_contact(text: str) -> Contact:
    prompt = (
        'Extract name, address and phone_number from the text. Return only a JSON object with keys '
        f'"name", "address", "phone_number".\n<text>{text}</text>'
    )
    show("structured-output prompt", prompt, "yellow")
    raw = llm.invoke(prompt).text
    return parse_contact(raw.strip().removeprefix("```json").removesuffix("```"))


if __name__ == "__main__":
    assert parse_contact('{"name": "Ann", "address": "1 Main St", "phone_number": "555"}').name == "Ann"
    try:
        parse_contact('{"name": "Ann"}')
        raise AssertionError("incomplete JSON must be rejected")
    except ValidationError:
        pass
    phase("Few-shot prompting")
    show("initial prompt", "The visuals were stunning, but the dialogue was weak.")
    show("few-shot output", few_shot_sentiment("The visuals were stunning, but the dialogue was weak."))
    phase("Step-back prompting")
    show("initial prompt", "write a three-sentence plot for a mystery novel set in a small town.")
    show("step-back output", step_back(
        "write a three-sentence plot for a mystery novel set in a small town.",
        "What are the key ingredients of a good detective story? List them briefly.",
    ))
    phase("Structured output")
    show("initial prompt", "Contact John Smith at 123 Main St, Anytown, CA or call (555) 123-4567.")
    show("structured output", extract_contact("Contact John Smith at 123 Main St, Anytown, CA or call (555) 123-4567."))
