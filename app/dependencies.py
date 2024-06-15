
from app.database import Session

def get_session():

    db = Session()

    try:
        yield db
    finally:
        db.close()
