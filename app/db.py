import datetime
import os

from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Database Setup ---
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Core Models (Required for the MVP)

class Template(Base):
    __tablename__ = "templates"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    doctype = Column(String, index=True, nullable=True)
    jurisdiction = Column(String, index=True, nullable=True)
    similaritytags = Column(ARRAY(String), nullable=True)
    bodymd = Column(Text, nullable=False)
    createdat = Column(DateTime, default=datetime.datetime.utcnow)
    variables = relationship("TemplateVariable", back_populates="template", cascade="all, delete-orphan")


class TemplateVariable(Base):
    __tablename__ = "template_variables"
    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=False)
    key = Column(String, index=True, nullable=False)
    label = Column(String, nullable=False)
    description = Column(Text)
    example = Column(String)
    required = Column(Boolean, default=True)

    # Added fields to fully match the spec
    dtype = Column(String, nullable=True)  # e.g., 'string', 'date', 'number'
    regex = Column(String, nullable=True)
    enum = Column(ARRAY(String), nullable=True)

    template = relationship("Template", back_populates="variables")


# --- Database Initializer and Session Dependency ---
def create_db_and_tables():
    """Creates all tables defined above in the database."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency to get a DB session for a request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

