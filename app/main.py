import os
import tempfile
from dotenv import load_dotenv
from typing import Dict, Any

from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from db import get_db, Template, TemplateVariable, create_db_and_tables
from schema import ExtractedVariable
from document_to_template import (
    process_document_to_template,
    build_or_update_vector_store,
    find_best_template_id,
    generate_human_friendly_questions,
    fill_template_with_answers
)

load_dotenv()
create_db_and_tables()

app = FastAPI(
    title="Legal Drafting Assistant: AI Legal Templating API",
    description="API for ingesting legal documents and generating reusable templates."
)

# CORS Middleware Setup
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

VECTOR_STORE = None

@app.on_event("startup")
def startup_event():
    """On startup, load all templates from DB and build the initial vector store."""
    global VECTOR_STORE
    db = next(get_db())
    all_templates = db.query(Template).all()
    if all_templates:
        VECTOR_STORE = build_or_update_vector_store(all_templates)
        print(f"Vector store initialized with {len(all_templates)} templates.")
    else:
        print("No existing templates found. Vector store is empty.")


# PHASE 1 ENDPOINT (UPLOAD & INGEST)

@app.post("/upload/", status_code=status.HTTP_201_CREATED, tags=["Templates"])
async def upload_and_process_document(db: Session = Depends(get_db), file: UploadFile = File(...)):
    """
    Uploads a .docx or .pdf, processes it into a template, saves it to the DB,
    and adds it to the searchable vector store.
    """
    file_extension = file.filename.split('.')[-1].lower()
    if file_extension not in ["docx", "pdf"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Only .docx and .pdf are supported.")

    tmp_path = None
    try:
        # Save uploaded file to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        # Process the document using the AI pipeline from document_to_template.py
        ai_template = process_document_to_template(tmp_path, file_extension)

        # Create SQLAlchemy ORM objects from the output
        new_template = Template(
            title=ai_template.title,
            description=ai_template.description,
            similaritytags=", ".join(ai_template.similaritytags),
            bodymd=ai_template.bodymd,
            doctype=file_extension
        )

        for var_data in ai_template.variables:
            new_var = TemplateVariable(**var_data.dict())
            new_template.variables.append(new_var)

        # Save the new template and its variables to the database
        db.add(new_template)
        db.commit()
        db.refresh(new_template)

        # Update the live vector store with the new template
        global VECTOR_STORE
        VECTOR_STORE = build_or_update_vector_store([new_template], store=VECTOR_STORE)
        print(f"Vector store updated with new template ID: {new_template.id}")

        return {"message": "Template created and indexed successfully", "template_id": new_template.id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process document. Error: {str(e)}")

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


# PHASE 2 ENDPOINT (DRAFTING)

class DraftRequest(BaseModel):
    query: str
    context: Dict[str, Any] = {}


@app.post("/draft/", tags=["Drafting"])
def start_or_continue_draft(request: DraftRequest, db: Session = Depends(get_db)):
    """Handles the multi-turn drafting process using RAG."""
    global VECTOR_STORE

    # 1. Find the best matching template using vector search
    template_id = find_best_template_id(request.query, VECTOR_STORE)
    if not template_id:
        raise HTTPException(status_code=404, detail="No suitable template found.")

    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template ID found but object not in DB.")

    # 2. Identify which variables required by the template are still missing
    required_vars = [ExtractedVariable(**v.__dict__) for v in template.variables]
    provided_keys = request.context.keys()
    missing_vars = [var for var in required_vars if var.key not in provided_keys]

    # 3. If variables are missing, return questions to the user
    if missing_vars:
        questions = generate_human_friendly_questions(missing_vars)
        return {
            "status": "in_progress",
            "message": "Please provide the following information.",
            "questions": questions,
            "template_id": template.id,
        }

    # 4. If all variables are present, generate the final draft
    final_draft = fill_template_with_answers(template.bodymd, request.context)
    return {
        "status": "complete",
        "message": "Draft generated successfully.",
        "draft": final_draft,
        "template_id": template.id,
    }

@app.get("/", tags=["Status"])
def root():
    return {"status": "ok", "message": "API is running"}
