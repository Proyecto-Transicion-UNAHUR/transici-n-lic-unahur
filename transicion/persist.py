from __future__ import annotations

import json
from transicion.models import SessionLocal, StudentSelection, CrActivityCompletion, AuditEvent

def save_student_selection(
    user_id: str,
    variant: str,
    subject_codes: list[str],
    activity_codes: list[str] | None = None,
) -> None:
    variant = (variant or "A").upper()
    activity_codes = activity_codes or []

    db = SessionLocal()
    try:
        # 1) Reemplazar selecciones
        db.query(StudentSelection).filter_by(user_id=user_id, variant=variant).delete()
        for code in subject_codes:
            code = (code or "").strip()
            if code:
                db.add(StudentSelection(user_id=user_id, variant=variant, subject_code=code, passed=True))

        # 2) Reemplazar actividades CR
        db.query(CrActivityCompletion).filter_by(user_id=user_id, variant=variant).delete()
        for code in activity_codes:
            code = (code or "").strip()
            if code:
                db.add(CrActivityCompletion(user_id=user_id, variant=variant, activity_code=code, completed=True))

        # 3) Registrar auditoría (misma sesión)
        db.add(AuditEvent(
            user_id=user_id,
            variant=variant,
            event_type="SAVE_SELECTION",
            payload_json=json.dumps({
                "passed_subjects_count": len(subject_codes),
                "passed_subjects": subject_codes[:200],
                "cr_activities_count": len(activity_codes),
                "cr_activities": activity_codes[:200],
            }, ensure_ascii=False),
        ))

        # 4) Un solo commit final
        db.commit()
    finally:
        db.close()
