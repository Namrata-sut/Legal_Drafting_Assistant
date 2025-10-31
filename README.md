# Legal Drafting Assistant AI
This project is an AI-powered legal tech application that transforms unstructured legal documents into structured, reusable templates. It features a FastAPI backend that uses Google's Gemini model for document analysis and a Next.js frontend for user interaction.

What's Inside
This repository contains the full source code for the application, including:

Backend: A FastAPI application that handles document ingestion, template creation, and the interactive drafting process.

Frontend: A Next.js application with two main components for uploading documents and drafting new ones via a chat interface.

Database: SQLAlchemy models and logic for a PostgreSQL database to store templates and their associated variables.

AI Logic: Integration with LangChain and Google Gemini for structured data extraction and a FAISS vector store for efficient template retrieval.

# Setup & Run Instructions
Follow these steps to set up and run the project locally.

1. Environment Setup
Clone the Repository:

bash
git clone <your-github-repo-link>
cd <repository-folder>
Create .env file: Create a .env file in the root of the project directory and add the following environment variables.

text
* Get your API key from Google AI Studio
```
    GOOGLE_API_KEY="your-gemini-api-key"
```
* Connection string for your PostgreSQL database
```
   DATABASE_URL="postgresql://user:password@host:port/dbname"
```
You can obtain a GOOGLE_API_KEY from Google AI Studio.

2. Backend Setup (FastAPI)
Install Dependencies: Navigate to the backend directory and install the required Python packages from requirements.txt.

* bash
```
pip install -r requirements.txt
```
This includes libraries like fastapi, sqlalchemy, langchain-google-genai, faiss-cpu, and others.

* Database Initialization: The application is configured to automatically create the necessary database tables upon startup, as defined in db.py. Ensure your DATABASE_URL is correctly configured.​

* Run the Backend Server:

bash
```
uvicorn main:app --reload
```
The API will be live at http://127.0.0.1:8000.

3. Frontend Setup (Next.js)
Install Dependencies: Navigate to the frontend directory and install the Node.js packages.

bash
```
npm install
```
or
```
yarn install
```
* Run the Frontend Server:
bash
```
npm run dev
```
or
```
yarn dev
```
The web interface will be accessible at http://localhost:3000.

# Architecture Overview
The application is built on a client-server architecture with two primary workflows: Template Ingestion and Document Drafting.

* Ingestion Flow:
This flow converts an uploaded document into a saved, searchable template.

1. File Upload: The user uploads a .docx or .pdf file via the Next.js frontend.​

2. Backend Processing: The FastAPI /upload endpoint receives the file.​

3. AI-Powered Extraction: The document's text is extracted and passed to the Gemini LLM using a structured output prompt (document_to_template.py). The LLM identifies key variables, generates a title, description, similarity tags, and rewrites the document body into Markdown with placeholder variables (e.g., {variable_key}).​

4. Database Storage: The extracted template and its variables are saved to the PostgreSQL database using SQLAlchemy models.​

5. Vector Indexing: The template's metadata (title, description, tags) is embedded and stored in an in-memory FAISS vector store for efficient similarity search.​

* Drafting Flow:
This multi-turn flow uses the stored templates to draft a new document based on user input.

1. Initial Query: The user starts a conversation in the chat interface with a request, like "Draft an NDA for a new project".​

2. Template Retrieval (RAG): The FastAPI /draft endpoint receives the query and uses the FAISS vector store to find the most relevant template based on semantic similarity.​

3. Q&A for Variables: The system identifies any required variables for the selected template that are not yet filled. It generates human-friendly questions and returns them to the user.​

4. Contextual Follow-up: The user's answers are collected and stored in a context object. The process repeats until all required variables are collected.

5. Final Draft Generation: Once all variables are provided, the system populates the template's Markdown body with the user's answers, generating the final document.​

6. Render Output: The completed Markdown draft is sent to the frontend for the user to view and copy.​

* Prompt Design Snippets
The core of the template extraction logic relies on a carefully designed prompt that instructs the LLM to act as a legal tech assistant and respond with a specific JSON structure.

The prompt is defined in document_to_template.py and uses LangChain's ChatPromptTemplate.​

python
```
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are an expert legal tech assistant. Your task is to analyze a legal document and convert it into a reusable Markdown template. Follow these steps precisely:
1. Read the document to create a title and description.
2. Identify all key entities (names, dates, amounts, etc.) as variables.
3. For each variable, define its 'key', 'label', 'description', 'example', and if it's 'required'.
4. Generate relevant 'similarity_tags' for future searches.
5. Rewrite the entire document as 'body_md' in Markdown format, replacing variables with `{variable_key}` placeholders.
Respond ONLY with the structured JSON object.""",
        ),
        ("human", "Here is the document text:\n---\n{document_text}"),
    ]
)

# The Pydantic schema 'DocumentTemplate' is then used with .with_structured_output()
# to enforce the JSON response format.
structured_llm = llm.with_structured_output(DocumentTemplate)
```