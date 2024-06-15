from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TodoBase(BaseModel):
    name: str
    description: str
    done: bool = False


class TodoCreate(TodoBase):
    pass

    class Config:
        orm_mode = True


class TodoUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    done: Optional[bool] = None

    class Config:
        orm_mode = True


class TodoRead(TodoBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True
