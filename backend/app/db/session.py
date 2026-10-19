from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from backend.app.core.config import settings
from backend.app.db.base import Base

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    echo=False,
)

Base.metadata.create_all(engine)
SessionFactory = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db_session() -> Generator[Session, None, None]:
    session = SessionFactory()

    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
