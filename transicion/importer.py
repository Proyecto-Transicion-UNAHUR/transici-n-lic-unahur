from __future__ import annotations

import csv
from io import StringIO

from transicion.models import SessionLocal, Subject2018A, Subject2018B, Subject2025, CrActivity


def _read_csv_bytes(data: bytes) -> csv.DictReader:
    text = data.decode("utf-8")
    return csv.DictReader(StringIO(text))


def import_subjects_2018A(csv_bytes: bytes) -> int:
    """Import subjects_2018A from a CSV payload.

    Expected headers: code,name,credits,hours_hint
    """
    reader = _read_csv_bytes(csv_bytes)
    db = SessionLocal()
    try:
        # Simple strategy: clear and reload
        db.query(Subject2018A).delete()
        n = 0
        for row in reader:
            code = (row.get("code") or "").strip()
            if not code:
                continue
            db.add(
                Subject2018A(
                    code=code,
                    name=(row.get("name") or "").strip(),
                    credits=int(row.get("credits") or 0),
                    hours_hint=(int(row["hours_hint"]) if (row.get("hours_hint") or "").strip() else None),
                )
            )
            n += 1
        db.commit()
        return n
    finally:
        db.close()


def import_subjects_2018B(csv_bytes: bytes) -> int:
    """Import subjects_2018B from a CSV payload.

    Expected headers: code,name,credits,hours_hint
    """
    reader = _read_csv_bytes(csv_bytes)
    db = SessionLocal()
    try:
        db.query(Subject2018B).delete()
        n = 0
        for row in reader:
            code = (row.get("code") or "").strip()
            if not code:
                continue
            db.add(
                Subject2018B(
                    code=code,
                    name=(row.get("name") or "").strip(),
                    credits=int(row.get("credits") or 0),
                    hours_hint=(int(row["hours_hint"]) if (row.get("hours_hint") or "").strip() else None),
                )
            )
            n += 1
        db.commit()
        return n
    finally:
        db.close()


def import_subjects_2025(csv_bytes: bytes) -> int:
    """Import subjects_2025 from a CSV payload.

    Expected headers: code,name,credits,hours_total
    """
    reader = _read_csv_bytes(csv_bytes)
    db = SessionLocal()
    try:
        db.query(Subject2025).delete()
        n = 0
        for row in reader:
            code = (row.get("code") or "").strip()
            if not code:
                continue
            db.add(
                Subject2025(
                    code=code,
                    name=(row.get("name") or "").strip(),
                    credits=int(row.get("credits") or 0),
                    hours_total=int(row.get("hours_total") or 0),
                )
            )
            n += 1
        db.commit()
        return n
    finally:
        db.close()


def import_cr_activities(csv_bytes: bytes) -> int:
    """Import CR activities mapping (old CR -> new CRE/ACA).

    Expected headers: code,description,cr_value,cre_value,variant
    variant can be empty for "all".
    """
    reader = _read_csv_bytes(csv_bytes)
    db = SessionLocal()
    try:
        db.query(CrActivity).delete()
        n = 0
        for row in reader:
            code = (row.get("code") or "").strip()
            if not code:
                continue
            variant = (row.get("variant") or "").strip() or None
            db.add(
                CrActivity(
                    code=code,
                    description=(row.get("description") or "").strip(),
                    cr_value=int(row.get("cr_value") or 0),
                    cre_value=int(row.get("cre_value") or 0),
                    variant=variant,
                )
            )
            n += 1
        db.commit()
        return n
    finally:
        db.close()
