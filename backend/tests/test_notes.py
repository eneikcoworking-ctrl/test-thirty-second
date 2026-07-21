import pytest
import time
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.main import app, get_db
from backend.models import Base, Note

# Create a clean in-memory SQLite database using StaticPool so connection is kept alive
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(name="db_session")
def fixture_db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(name="client")
def fixture_client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

def test_unauthorized_access(client):
    # Retrieve notes list without authentication header
    response = client.get("/notes")
    assert response.status_code == 401

    # Create note without authentication header
    response = client.post("/notes", json={"title": "Test Title", "body": "Test Body"})
    assert response.status_code == 401

def test_create_note(client):
    headers = {"X-User-Id": "alice"}
    payload = {"title": "Alice Note", "body": "This is Alice's first note."}

    response = client.post("/notes", json=payload, headers=headers)
    assert response.status_code == 201

    data = response.json()
    assert data["title"] == "Alice Note"
    assert data["body"] == "This is Alice's first note."
    assert data["owner_id"] == "alice"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data

def test_list_notes_only_returns_owners_notes_and_sorted(client, db_session):
    # Pre-populate notes
    # Alice has 3 notes created at different times
    # Note 1: Older
    # Note 2: Newest updated
    # Note 3: Medium age

    now = datetime.utcnow()

    # We will create notes manually and add them to the database
    note1 = Note(
        title="First Note of Alice",
        body="Content 1",
        owner_id="alice",
        created_at=now - timedelta(hours=2),
        updated_at=now - timedelta(hours=2)
    )
    note2 = Note(
        title="Second Note of Alice (Most Recently Updated)",
        body="Content 2",
        owner_id="alice",
        created_at=now - timedelta(hours=1),
        updated_at=now  # Newest update
    )
    note3 = Note(
        title="Third Note of Alice",
        body="Content 3",
        owner_id="alice",
        created_at=now - timedelta(minutes=30),
        updated_at=now - timedelta(minutes=30)
    )
    # Bob has a note
    bob_note = Note(
        title="Bob's Secret Note",
        body="Bob's content",
        owner_id="bob",
        created_at=now,
        updated_at=now
    )

    db_session.add_all([note1, note2, note3, bob_note])
    db_session.commit()

    # Alice requests her notes
    headers = {"Authorization": "Bearer alice"}
    response = client.get("/notes", headers=headers)
    assert response.status_code == 200

    notes = response.json()
    # Should only return Alice's notes (3 notes, not Bob's)
    assert len(notes) == 3
    for n in notes:
        assert n["owner_id"] == "alice"

    # Should be sorted newest-first (by updated_at desc)
    # Newest: note2 (updated_at = now)
    # Second: note3 (updated_at = now - 30m)
    # Third: note1 (updated_at = now - 2h)
    assert notes[0]["id"] == note2.id
    assert notes[1]["id"] == note3.id
    assert notes[2]["id"] == note1.id

def test_search_notes_by_title_filter(client, db_session):
    # Pre-populate notes
    now = datetime.utcnow()
    note1 = Note(title="Python FastAPI Tutorial", body="Content", owner_id="alice", created_at=now, updated_at=now)
    note2 = Note(title="JavaScript Design Patterns", body="Content", owner_id="alice", created_at=now, updated_at=now)
    note3 = Note(title="Database Systems", body="Content", owner_id="alice", created_at=now, updated_at=now)

    db_session.add_all([note1, note2, note3])
    db_session.commit()

    headers = {"Authorization": "Bearer alice"}

    # Search for "design" (case-insensitive substring match)
    response = client.get("/notes?q=design", headers=headers)
    assert response.status_code == 200
    notes = response.json()
    assert len(notes) == 1
    assert notes[0]["title"] == "JavaScript Design Patterns"

    # Search for "tutorial"
    response = client.get("/notes?q=tutorial", headers=headers)
    assert response.status_code == 200
    notes = response.json()
    assert len(notes) == 1
    assert notes[0]["title"] == "Python FastAPI Tutorial"

    # Search for "NonExistent"
    response = client.get("/notes?q=NonExistent", headers=headers)
    assert response.status_code == 200
    notes = response.json()
    assert len(notes) == 0

def test_get_individual_note(client, db_session):
    now = datetime.utcnow()
    note = Note(title="Secrets", body="Top secret", owner_id="alice", created_at=now, updated_at=now)
    db_session.add(note)
    db_session.commit()
    db_session.refresh(note)

    # Alice retrieves her note (succeeds)
    response = client.get(f"/notes/{note.id}", headers={"Authorization": "Bearer alice"})
    assert response.status_code == 200
    assert response.json()["title"] == "Secrets"

    # Bob tries to retrieve Alice's note (403 Forbidden)
    response = client.get(f"/notes/{note.id}", headers={"Authorization": "Bearer bob"})
    assert response.status_code == 403

    # Non-existent note (404 Not Found)
    response = client.get("/notes/999", headers={"Authorization": "Bearer alice"})
    assert response.status_code == 404

def test_update_note(client, db_session):
    now = datetime.utcnow()
    note = Note(title="Draft Note", body="Initial content", owner_id="alice", created_at=now, updated_at=now)
    db_session.add(note)
    db_session.commit()
    db_session.refresh(note)

    payload = {"title": "Updated Note", "body": "Modified content"}

    # Bob tries to update Alice's note (403 Forbidden)
    response = client.put(f"/notes/{note.id}", json=payload, headers={"Authorization": "Bearer bob"})
    assert response.status_code == 403

    # Alice updates her note (succeeds)
    response = client.put(f"/notes/{note.id}", json=payload, headers={"Authorization": "Bearer alice"})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Note"
    assert data["body"] == "Modified content"

    # Non-existent note (404 Not Found)
    response = client.put("/notes/999", json=payload, headers={"Authorization": "Bearer alice"})
    assert response.status_code == 404

def test_delete_note(client, db_session):
    now = datetime.utcnow()
    note = Note(title="To be deleted", body="Temp content", owner_id="alice", created_at=now, updated_at=now)
    db_session.add(note)
    db_session.commit()
    db_session.refresh(note)

    # Bob tries to delete Alice's note (403 Forbidden)
    response = client.delete(f"/notes/{note.id}", headers={"Authorization": "Bearer bob"})
    assert response.status_code == 403

    # Alice deletes her note (240 No Content / 204 No Content)
    response = client.delete(f"/notes/{note.id}", headers={"Authorization": "Bearer alice"})
    assert response.status_code == 204

    # Verify note is deleted from database
    deleted_note = db_session.query(Note).filter(Note.id == note.id).first()
    assert deleted_note is None

    # Non-existent note (404 Not Found)
    response = client.delete("/notes/999", headers={"Authorization": "Bearer alice"})
    assert response.status_code == 404
