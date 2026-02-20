from __future__ import annotations
import csv
import logging
from io import StringIO
from sqlalchemy.orm import Session
from transicion.models import SessionLocal, Subject2018A, Subject2018B, Subject2025, CrActivity

logger = logging.getLogger(__name__)

# --- NUEVA FUNCIÓN VALIDADORA ---
def validate_headers(reader: csv.DictReader, required_headers: list[str]):
    """Verifica que todas las columnas requeridas estén presentes en el CSV."""
    actual_headers = [h.strip().lower() for h in (reader.fieldnames or [])]
    missing = [h for h in required_headers if h.lower() not in actual_headers]
    if missing:
        raise ValueError(f"Faltan las siguientes columnas requeridas: {', '.join(missing)}")

def _read_csv_bytes(data: bytes) -> csv.DictReader:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        text = data.decode("latin-1")
    return csv.DictReader(StringIO(text))

def _safe_int(value, default=0) -> int:
    if value is None: return default
    try:
        clean_val = str(value).strip().split('.')[0]
        return int(clean_val) if clean_val else default
    except (ValueError, TypeError):
        return default

# --- FUNCIONES DE IMPORTACIÓN ACTUALIZADAS ---

def import_subjects_2018A(csv_bytes: bytes) -> int:
    reader = _read_csv_bytes(csv_bytes)
    # Validamos antes de procesar
    validate_headers(reader, ["code", "name", "credits", "hours_hint"])
    
    db: Session = SessionLocal()
    try:
        db.query(Subject2018A).delete()
        subjects = [
            Subject2018A(
                code=row["code"].strip(),
                name=(row.get("name") or "S/N").strip(),
                credits=_safe_int(row.get("credits")),
                hours_hint=_safe_int(row.get("hours_hint"), default=None)
            ) for row in reader if row.get("code")
        ]
        db.bulk_save_objects(subjects)
        db.commit()
        return len(subjects)
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def import_subjects_2018B(csv_bytes: bytes) -> int:
    reader = _read_csv_bytes(csv_bytes)
    validate_headers(reader, ["code", "name", "credits", "hours_hint"])
    
    db: Session = SessionLocal()
    try:
        db.query(Subject2018B).delete()
        subjects = [
            Subject2018B(
                code=row["code"].strip(),
                name=(row.get("name") or "S/N").strip(),
                credits=_safe_int(row.get("credits")),
                hours_hint=_safe_int(row.get("hours_hint"), default=None)
            ) for row in reader if row.get("code")
        ]
        db.bulk_save_objects(subjects)
        db.commit()
        return len(subjects)
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def import_subjects_2025(csv_bytes: bytes) -> int:
    reader = _read_csv_bytes(csv_bytes)
    validate_headers(reader, ["code", "name", "credits", "hours_total"])
    
    db: Session = SessionLocal()
    try:
        db.query(Subject2025).delete()
        subjects = [
            Subject2025(
                code=row["code"].strip(),
                name=(row.get("name") or "S/N").strip(),
                credits=_safe_int(row.get("credits")),
                hours_total=_safe_int(row.get("hours_total"))
            ) for row in reader if row.get("code")
        ]
        db.bulk_save_objects(subjects)
        db.commit()
        return len(subjects)
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def import_cr_activities(csv_bytes: bytes) -> int:
    reader = _read_csv_bytes(csv_bytes)
    validate_headers(reader, ["code", "description", "cr_value", "cre_value"])
    
    db: Session = SessionLocal()
    try:
        db.query(CrActivity).delete()
        activities = [
            CrActivity(
                code=row["code"].strip(),
                description=(row.get("description") or "S/D").strip(),
                cr_value=_safe_int(row.get("cr_value")),
                cre_value=_safe_int(row.get("cre_value")),
                variant=(row.get("variant") or "").strip().upper() or None
            ) for row in reader if row.get("code")
        ]
        db.bulk_save_objects(activities)
        db.commit()
        return len(activities)
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()