from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from app.config import settings


engine = create_engine(
    settings.DATABASE_URI, pool_pre_ping=True, pool_size=25, max_overflow=5
)
relica_engine = create_engine(
    settings.SLAVE_DATABASE_URI, pool_pre_ping=True, pool_size=25, max_overflow=5
)


db_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

ReadonlySession = sessionmaker(autocommit=False, autoflush=False, bind=relica_engine)