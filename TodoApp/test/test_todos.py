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

def test_read_one_authenticated(test_todos):
    response = client.get(f"/todo/{test_todos.id}")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"id": test_todos.id, "title": test_todos.title, "description": test_todos.description, "priority": test_todos.priority, "complete": test_todos.complete, "owner_id": test_todos.owner_id}

def test_read_one_authenticated_not_found():
    response = client.get("/todo/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Todo not found."}

def test_create_todo_authenticated(test_todos):
    response_data = {
        "title": "New Todo",
        "description": "This is a new todo",
        "priority": 2,
        "complete": False
    }
    response = client.post("/todo/", json=response_data)
    assert response.status_code == status.HTTP_201_CREATED

    db = TestingSessionLocal()
    model = db.query(Todos).filter(Todos.id == 2).first()
    assert model.title == response_data["title"]
    assert model.description == response_data["description"]
    assert model.priority == response_data["priority"]
    assert model.complete == response_data["complete"]

  
def test_update_todo(test_todos):
    response_data = {
        "title": "Updated Todo",
        "description": "This is an updated todo",
        "priority": 4,
        "complete": True
    }
    response = client.put(f"/todo/1", json=response_data)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    db = TestingSessionLocal()
    model = db.query(Todos).filter(Todos.id == 1).first()
    assert model.title == "Updated Todo"

def test_update_todo_not_found(test_todos):
    response_data = {
        "title": "Updated Todo",
        "description": "This is an updated todo",
        "priority": 4,
        "complete": True
    }
    response = client.put(f"/todo/999", json=response_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Todo not found"}

def test_delete_todo(test_todos):
    response = client.delete(f"/todo/{test_todos.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    db = TestingSessionLocal()
    model = db.query(Todos).filter(Todos.id == test_todos.id).first()
    assert model is None

def test_delete_todo_not_found():
    response = client.delete("/todo/999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Todo not found"}