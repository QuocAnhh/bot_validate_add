import logging
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import DATABASE_URL

logger = logging.getLogger(__name__)

_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        if not DATABASE_URL:
            logger.warning("DATABASE_URL is not configured; database features are disabled.")
            return None
        # Use pool_pre_ping to avoid stale connections
        _engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
    return _engine


def get_session() -> Optional[sessionmaker]:
    global _SessionLocal
    engine = get_engine()
    if engine is None:
        return None
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return _SessionLocal


def init_db(Base) -> None:
    engine = get_engine()
    if engine is None:
        return
    Base.metadata.create_all(bind=engine) 