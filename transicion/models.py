from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import DateTime
from datetime import datetime

# --- DB path (absolute, stable) ---
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "transicion.db"
DB_URL = "sqlite:///%s" % DB_PATH.as_posix()

engine = create_engine(
    DB_URL,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    user_id = Column(String, index=True, nullable=False)
    variant = Column(String, index=True, nullable=False)  # "A" o "B"

    event_type = Column(String, index=True, nullable=False)  # "SAVE_SELECTION", "CALC", etc.
    payload_json = Column(String, nullable=True)             # JSON string con detalles


class Subject2018A(Base):
    __tablename__ = "subjects_2018A"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    credits = Column(Integer, nullable=False, default=0)
    hours_hint = Column(Integer, nullable=True)


class Subject2018B(Base):
    __tablename__ = "subjects_2018B"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    credits = Column(Integer, nullable=False, default=0)
    hours_hint = Column(Integer, nullable=True)


class Subject2025(Base):
    __tablename__ = "subjects_2025"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    credits = Column(Integer, nullable=False, default=0)
    hours_total = Column(Integer, nullable=False, default=0)


class StudentSelection(Base):
    __tablename__ = "student_selection"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, index=True, nullable=False)
    variant = Column(String, index=True, nullable=False)  # "A" o "B"
    subject_code = Column(String, index=True, nullable=False)
    passed = Column(Boolean, default=False, nullable=False)


class CrActivity(Base):
    __tablename__ = "cr_activities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String, unique=True, index=True, nullable=False)  # CR_003
    description = Column(String, nullable=False)
    cr_value = Column(Integer, nullable=False, default=0)
    cre_value = Column(Integer, nullable=False, default=0)
    variant = Column(String, nullable=True)  # "B" o None


class CrActivityCompletion(Base):
    __tablename__ = "cr_activity_completions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, index=True, nullable=False)
    variant = Column(String, index=True, nullable=False)
    activity_code = Column(String, index=True, nullable=False)
    completed = Column(Boolean, default=True, nullable=False)


def init_db() -> None:
    """Create missing tables in transicion.db."""
    Base.metadata.create_all(bind=engine)
