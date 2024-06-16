from fastapi import FastAPI
from app.schemas import TodoCreate, TodoRead
from app.dependencies import get_session, get_readonly_session
from sqlalchemy.orm import Session
from fastapi import Depends, status
from fastapi.exceptions import HTTPException
from app.models import TodoModel
from typing import List
from fastapi.responses import ORJSONResponse

app = FastAPI()


@app.get("/")
def healthcheck(db_session: Session = Depends(get_session)):
    try:
        db_session.execute("SELECT NOW();")

        return "OK"
    except Exception:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail="Db is down")


@app.get("/todos/", response_model=List[TodoRead], response_class=ORJSONResponse)
async def todos(db_session: Session = Depends(get_readonly_session)):
    db_todos = (
        db_session.query(TodoModel)
        .order_by(TodoModel.created_at.desc())
        .limit(200)
        .all()
    )

    return db_todos


@app.get("/todos/{id}", response_model=TodoRead, response_class=ORJSONResponse)
async def todo_index(id: int, db_session: Session = Depends(get_session)):
    db_todo = db_session.query(TodoModel).filter(TodoModel.id == id).one()

    return db_todo


@app.post("/todos/")
async def make_todo(todo: TodoCreate, db_session: Session = Depends(get_session)):
    db_todo = TodoModel(**todo.dict())
    db_session.add(db_todo)

    db_session.commit()
    db_session.refresh(db_todo)

    return db_todo


@app.put("/todos/{id}")
async def mark_todo_as_done(id: int, db_session: Session = Depends(get_session)):
    db_todo = db_session.query(TodoModel).filter(TodoModel.id == id).one()

    db_todo.done = True

    db_session.add(db_todo)
    db_session.commit()

    db_session.refresh(db_todo)

    return db_todo


@app.delete("/todos/{id}")
async def delete_todo(id: int, db_session: Session = Depends(get_session)):
    db_session.query(TodoModel).filter(TodoModel.id == id).delete()

    return "OK"
