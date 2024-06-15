
from app.database import Session, ReadonlySession

def get_session():

    db = Session()

    try:
        yield db
    finally:
        db.close()

def get_readonly_session():
    db = ReadonlySession()

    try:
        yield db
    finally:
        db.close()