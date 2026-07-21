import os
import datetime
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Header, status, Query
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, Field

from backend.models import Base, Note

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./notes.db")
# Using check_same_thread=False for SQLite
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Project Notes API",
    description="Backend API for Project Notes management",
    version="1.0.0"
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic Schemas
class NoteCreate(BaseModel):
    title: str = Field(..., max_length=100, description="Short title of the note")
    body: str = Field(..., description="Main body text of the note")

class NoteUpdate(BaseModel):
    title: str = Field(..., max_length=100, description="Short title of the note")
    body: str = Field(..., description="Main body text of the note")

class NoteResponse(BaseModel):
    id: int
    title: str
    body: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    owner_id: str

    class Config:
        from_attributes = True

# Authentication Dependency
# Accepts Authorization Bearer token (where token is the owner_id) or X-User-Id header.
# Returns the authenticated owner_id.
def get_current_user(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id")
) -> str:
    user_id = None
    if authorization and authorization.lower().startswith("bearer "):
        user_id = authorization[7:].strip()
    elif x_user_id:
        user_id = x_user_id.strip()

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials"
        )
    return user_id

@app.post("/notes", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
def create_note(
    note_in: NoteCreate,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    note = Note(
        title=note_in.title,
        body=note_in.body,
        owner_id=current_user
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note

@app.get("/notes", response_model=List[NoteResponse])
def list_notes(
    q: Optional[str] = Query(None, description="Search term to filter notes by title"),
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Retrieve only the current user's notes
    query = db.query(Note).filter(Note.owner_id == current_user)

    # Filter by title if query parameter 'q' is provided
    if q:
        query = query.filter(Note.title.ilike(f"%{q}%"))

    # Sort newest-first (updated_at desc, then created_at desc)
    notes = query.order_by(desc(Note.updated_at), desc(Note.created_at)).all()
    return notes

@app.get("/notes/{note_id}", response_model=NoteResponse)
def get_note(
    note_id: int,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )

    # Check ownership
    if note.owner_id != current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requester is not the owner of this note"
        )
    return note

@app.put("/notes/{note_id}", response_model=NoteResponse)
def update_note(
    note_id: int,
    note_in: NoteUpdate,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )

    # Check ownership
    if note.owner_id != current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requester is not the owner of this note"
        )

    note.title = note_in.title
    note.body = note_in.body
    # Explicitly update the updated_at timestamp to ensure it updates even if content is identical
    note.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(note)
    return note

@app.delete("/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    note_id: int,
    current_user: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )

    # Check ownership
    if note.owner_id != current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requester is not the owner of this note"
        )

    db.delete(note)
    db.commit()
    return
