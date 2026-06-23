import uuid
from contextlib import contextmanager
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Integer, String, Text, create_engine, update as sql_update
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    youtube_url = Column(String(2048), nullable=False)
    status = Column(String(32), default="queued", nullable=False)
    progress = Column(Integer, default=0, nullable=False)
    error = Column(Text, nullable=True)
    clips = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


_engine = None


def get_engine():
    global _engine
    if _engine is None:
        from backend.config import DATABASE_URL
        _engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    return _engine


def init_db():
    Base.metadata.create_all(get_engine())


@contextmanager
def get_session():
    Session = sessionmaker(bind=get_engine())
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def update_job(job_id: str, **kwargs) -> None:
    kwargs["updated_at"] = datetime.utcnow()
    with get_session() as session:
        session.execute(sql_update(Job).where(Job.id == job_id).values(**kwargs))
