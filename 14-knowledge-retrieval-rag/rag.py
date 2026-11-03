from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from step_logger import phase, show

MODEL = "gemini-3.5-flash-lite"
EMBEDDING_MODEL = "gemini-embedding-001"
TOP_K = 3

KNOWLEDGE_BASE = [
    Document(
        page_content="Remote work policy: employees may work remotely up to 3 days per week with manager approval.",
        metadata={"source": "hr-policy-2025.md", "date": "2025-01-15", "kind": "official policy"},
    ),
    Document(
        page_content="Blog: during 2020 everyone is fully remote until further notice!",
        metadata={"source": "blog-2020-03.md", "date": "2020-03-20", "kind": "blog post"},
    ),
    Document(
        page_content="Project Alpha proposal: requested Q1 budget of 50,000 EUR.",
        metadata={"source": "alpha-proposal.md", "date": "2024-11-02", "kind": "proposal"},
    ),
    Document(
        page_content="Project Alpha final financial report: approved Q1 budget was 65,000 EUR.",
        metadata={"source": "alpha-financials.md", "date": "2025-04-10", "kind": "financial report"},
    ),
    Document(
        page_content="Office hours: the Madrid office is open 8:00-19:00 on weekdays.",
        metadata={"source": "facilities.md", "date": "2024-06-01", "kind": "facilities note"},
    ),
]

ANSWER_PROMPT = """Answer the question using ONLY the sources below.
If sources conflict, prefer official or final documents over drafts and blogs, and newer over older; say which you chose.
Cite sources as [source]. If the sources don't contain the answer, say you don't know.

Sources:
{context}

Question: {question}"""


def build_retriever(embeddings: Embeddings):
    store = InMemoryVectorStore(embeddings)
    store.add_documents(KNOWLEDGE_BASE)
    return store.as_retriever(search_kwargs={"k": TOP_K})


def format_sources(documents: list[Document]) -> str:
    return "\n".join(
        f"[{d.metadata['source']}] ({d.metadata['kind']}, {d.metadata['date']}): {d.page_content}" for d in documents
    )


def ask(question: str, retriever, llm) -> str:
    phase(f"Retrieve: {question}")
    documents = retriever.invoke(question)
    show("retrieved", [{"source": d.metadata["source"], "kind": d.metadata["kind"], "date": d.metadata["date"], "text": d.page_content} for d in documents])
    phase("Augment: build prompt")
    context = format_sources(documents)
    prompt = ANSWER_PROMPT.format(context=context, question=question)
    show("prompt", prompt)
    phase("Generate")
    return llm.invoke(prompt).text


if __name__ == "__main__":
    retriever = build_retriever(GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL))
    llm = ChatGoogleGenerativeAI(model=MODEL)
    for question in ["What is our remote work policy?", "What was Project Alpha's Q1 budget?", "Who won the 2030 World Cup?"]:
        show("initial prompt", question)
        print(f"Q: {question}\nA: {ask(question, retriever, llm)}\n")
