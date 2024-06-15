from sqlalchemy import Column
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from sqlalchemy import Integer, String, Boolean, DateTime
from sqlalchemy import func


@as_declarative()
class Base:
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()


class TodoModel(Base):
    __tablename__ = "todos"
    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String, nullable=False, default="United todo")
    description: str = Column(String, nullable=False, default="")

    done: bool = Column(Boolean, index=True)

    created_at = Column(DateTime, nullable=True, server_default=func.now())
    updated_at = Column(DateTime, nullable=True, server_onupdate=func.now())
