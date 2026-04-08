"""SQLAlchemy async engine + session factory."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import config


class Base(DeclarativeBase):
    pass


engine = create_engine(
    config.settings.database_url,
    connect_args={"check_same_thread": False},  # SQLite only
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables."""
    from app.models import virtual_key, request_log, model_config  # noqa: F401
    Base.metadata.create_all(bind=engine)
