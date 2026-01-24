# transicion/maintenance.py
from __future__ import annotations

from transicion.models import (
    SessionLocal,
    Subject2018A,
    Subject2018B,
    CrActivity,
    StudentSelection,
    CrActivityCompletion,
)


def cleanup_orphan_selections() -> dict:
    """
    Elimina selecciones huérfanas:
      - student_selection.subject_code que no existe en el catálogo 2018 correspondiente (A o B)
      - cr_activity_completions.activity_code que no existe en cr_activities

    Retorna un dict con contadores de filas eliminadas.
    """
    db = SessionLocal()
    try:
        # Códigos válidos por variante
        codes_2018A = {r[0] for r in db.query(Subject2018A.code).all()}
        codes_2018B = {r[0] for r in db.query(Subject2018B.code).all()}
        codes_cr = {r[0] for r in db.query(CrActivity.code).all()}

        # Selecciones huérfanas en student_selection:
        # - variant A: borrar subject_code no presente en subjects_2018A
        # - variant B: borrar subject_code no presente en subjects_2018B
        orphan_sel_A = (
            db.query(StudentSelection)
            .filter(StudentSelection.variant == "A")
            .filter(~StudentSelection.subject_code.in_(codes_2018A))
        )
        orphan_sel_B = (
            db.query(StudentSelection)
            .filter(StudentSelection.variant == "B")
            .filter(~StudentSelection.subject_code.in_(codes_2018B))
        )

        deleted_sel_A = orphan_sel_A.delete(synchronize_session=False)
        deleted_sel_B = orphan_sel_B.delete(synchronize_session=False)

        # Actividades CR huérfanas
        orphan_cr = (
            db.query(CrActivityCompletion)
            .filter(~CrActivityCompletion.activity_code.in_(codes_cr))
        )
        deleted_cr = orphan_cr.delete(synchronize_session=False)

        db.commit()

        return {
            "deleted_student_selection_A": int(deleted_sel_A or 0),
            "deleted_student_selection_B": int(deleted_sel_B or 0),
            "deleted_cr_activity_completions": int(deleted_cr or 0),
        }
    finally:
        db.close()
