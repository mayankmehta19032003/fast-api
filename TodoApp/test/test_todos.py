from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from database import Base
from main import app
from routers.todos import get_db, get_current_user
from fastapi.testclient import TestClient
from fastapi import status
import pytest
from models import Todos


SQLALCHEMY_DATABASE_URI = 'sqlite:///./testdb.db'

engine = create_engine(SQLALCHEMY_DATABASE_URI, connect_args={"check_same_thread": False},poolclass=StaticPool)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

def override_get_current_user():
    return {"username": "t", "id": 1,"user_role":"admin"}

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)

@pytest.fixture
def test_todos():
    todo = Todos(title="Test Todo", description="This is a test todo", priority=3, complete=False, owner_id=1)
    db = TestingSessionLocal()
    db.add(todo)
    db.commit()
    yield todo
    with engine.connect() as connection:
        connection.execute(text("DELETE FROM todos;"))
        connection.commit()

def test_read_all_authenticated(test_todos):
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [{"id": test_todos.id, "title": test_todos.title, "description": test_todos.description, "priority": test_todos.priority, "complete": test_todos.complete, "owner_id": test_todos.owner_id}]
