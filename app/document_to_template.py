import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from schema import DocumentTemplate, ExtractedVariable
from typing import List

load_dotenv()


# PHASE 1
def process_document_to_template(file_path: str, file_type: str):
    """
        Loads a document, extracts text, and uses an LLM to generate a structured template.
    """
    # 1. Load document text
    if file_type == "pdf":
        loader = PyPDFLoader(file_path)
    elif file_type == "docx":
        loader = Docx2txtLoader(file_path)
    else:
        raise ValueError("Unsupported file type")

    documents = loader.load()
    doc_text = "\n".join([doc.page_content for doc in documents])

    # 2. Verify API key is loaded
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables")

    print(f"API Key loaded: {api_key[:10]}...")


    # 3. Initialize LLM with explicit API key
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        google_api_key=api_key
    )
    structured_llm = llm.with_structured_output(DocumentTemplate)

    # 4. Create the prompt for the LLM
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert legal tech assistant. Your task is to analyze a legal document and convert it into a reusable Markdown template.
        Follow these steps precisely:
        1. Read the document to create a `title` and `description`.
        2. Identify all key entities (names, dates, amounts,..., etc.) as `variables`.
        3. For each variable, define its `key`, `label`, `description`, `example`, and if it's `required`.
        4. Generate relevant `similaritytags` for future searches.
        5. Rewrite the entire document as `bodymd` in Markdown format, replacing variables with `{{variable_key}}` placeholders.
        Respond ONLY with the structured JSON object."""),
        ("human", "Here is the document text:\n\n---\n\n{document_text}")
    ])

    # 5. Create the chain and invoke it
    chain = prompt | structured_llm
    ai_template = chain.invoke({"document_text": doc_text})

    return ai_template


# PHASE 2
# Global Variables for Embeddings and Vector Store
EMBEDDING_MODEL = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cpu"}
)
VECTOR_STORE = None

def build_or_update_vector_store(db_templates: List, store: FAISS = None) -> FAISS:
    """Builds a new FAISS vector store or updates an existing one."""
    docs = []
    for t in db_templates:
        content = f"Title: {t.title}\nDescription: {t.description}\nTags: {t.similaritytags}"
        doc = Document(page_content=content, metadata={"template_id": t.id})
        docs.append(doc)
    if not docs:
        return store
    if store:
        store.add_documents(docs)
        return store
    else:
        return FAISS.from_documents(docs, EMBEDDING_MODEL)

def find_best_template_id(query: str, store: FAISS) -> int | None:
    """Performs a similarity search and returns the ID of the best matching template."""
    if not store:
        return None
    results = store.similarity_search(query, k=1)
    if not results:
        return None
    return results[0].metadata.get("template_id")

def generate_human_friendly_questions(missing_vars: List[ExtractedVariable]) -> List[str]:
    """Uses an LLM to turn variable metadata into human-friendly questions."""
    if not missing_vars:
        return []
    questions = []
    for var in missing_vars:
        question = f"Regarding '{var.label}', what is the value? (For example: {var.example or '...'})"
        questions.append(question)
    return questions

def fill_template_with_answers(template_body: str, user_answers: dict) -> str:
    """Fills the template's placeholders with the provided answers."""
    filled_body = template_body
    for key, value in user_answers.items():
        placeholder = f"{{{{{key}}}}}"
        filled_body = filled_body.replace(placeholder, str(value))
    return filled_body
