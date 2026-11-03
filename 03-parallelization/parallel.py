import asyncio

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_google_genai import ChatGoogleGenerativeAI

from step_logger import StepLogger, phase, show

MODEL = "gemini-3.5-flash-lite"

llm = ChatGoogleGenerativeAI(model=MODEL)


def task(instruction: str):
    return ChatPromptTemplate.from_messages([("system", instruction), ("user", "{topic}")]) | llm | StrOutputParser()


fan_out = RunnableParallel(
    summary=task("Summarize this topic in two sentences."),
    questions=task("Ask three interesting questions about this topic."),
    key_terms=task("List 5 key terms for this topic, comma separated."),
    topic=RunnablePassthrough(),
)

synthesize = ChatPromptTemplate.from_template(
    "Topic: {topic}\nSummary: {summary}\nQuestions: {questions}\nKey terms: {key_terms}\n\n"
    "Write one coherent paragraph that uses all of the above."
) | llm | StrOutputParser()

steps = StepLogger()

pipeline = steps.step("fan-out input") | fan_out | steps.step("fan-in: branch results") | synthesize | steps.step("synthesis")


if __name__ == "__main__":
    phase("Fan-out: summary, questions, key_terms run in parallel, then fan-in synthesis")
    show("initial prompt", "The history of space exploration")
    result = asyncio.run(pipeline.ainvoke("The history of space exploration"))
    phase("Final paragraph")
    print(result)
