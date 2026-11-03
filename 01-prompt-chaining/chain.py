from pydantic import BaseModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from step_logger import StepLogger, phase, show

MODEL = "gemini-3.5-flash-lite"

steps = StepLogger()

class LaptopSpecs(BaseModel):
    cpu: str
    memory: str
    storage: str

llm = ChatGoogleGenerativeAI(model=MODEL)

extract_specs = (
    ChatPromptTemplate.from_template("Extract the technical specifications from this text:\n\n{text}")
    | llm
    | StrOutputParser()
)

structure_specs = ChatPromptTemplate.from_template(
    "Map these specifications to cpu, memory and storage:\n\n{specifications}"
) | llm.with_structured_output(LaptopSpecs)

draft_email = (
    ChatPromptTemplate.from_template(
        "Write a three-sentence product announcement email for a laptop with "
        "CPU: {cpu}, memory: {memory}, storage: {storage}."
    )
    | llm
    | StrOutputParser()
)

pipeline = (
    steps.step("input")
    | {"specifications": extract_specs}
    | steps.step("extract_specs")
    | structure_specs
    | steps.step("structure_specs")
    | (lambda specs: specs.model_dump())
    | steps.step("model_dump")
    | draft_email
    | steps.step("draft_email")
)


if __name__ == "__main__":
    text = "The new laptop has a 3.5 GHz octa-core processor, 16GB of RAM, and a 1TB NVMe SSD."
    phase("Prompt chaining: extract, structure, draft")
    show("initial prompt", text)
    result = pipeline.invoke({"text": text})
    phase("Final email")
    print(result)
