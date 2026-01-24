import pandas as pd
import streamlit as st

from transicion.models import init_db, SessionLocal
from transicion.importer import (
    import_subjects_2018A,
    import_subjects_2018B,
    import_subjects_2025,
    import_cr_activities,
)
from transicion.models import Subject2018A, Subject2018B, Subject2025, CrActivity
from transicion.persist import save_student_selection
from transicion.calculator import run_calc, PLAN2018_TOTAL_HOURS, PLAN2025_TOTAL_HOURS, ACA_TOTAL_REQUIRED, CREDITS_TO_HOURS
from transicion.pdf_report import build_pdf_bytes

from transicion.maintenance import cleanup_orphan_selections
import pandas as pd
from transicion.models import AuditEvent

def get_db():
    return SessionLocal()


# --- session defaults ---
for k, v in {
    "step": 1,
    "nombre": "",
    "dni": "",
    "variant": "A",
    "user_id": "",
}.items():
    st.session_state.setdefault(k, v)


def render_admin():
    init_db()
    st.title("Administración")
    
    st.header("Administración")
    st.caption("Importación de catálogos (CSV)")

    db = get_db()
    try:
        st.write("2018A:", db.query(Subject2018A).count())
        st.write("2018B:", db.query(Subject2018B).count())
        st.write("2025:", db.query(Subject2025).count())
        st.write("CR→CRE:", db.query(CrActivity).count())
    finally:
        db.close()

    up = st.file_uploader("subjects_2018A.csv", type=["csv"], key="up2018a")
    if up and st.button("Importar 2018A"):
        n = import_subjects_2018A(up.getvalue())
        st.success(f"Importado 2018A: {n} filas")

    up = st.file_uploader("subjects_2018B.csv", type=["csv"], key="up2018b")
    if up and st.button("Importar 2018B"):
        n = import_subjects_2018B(up.getvalue())
        st.success(f"Importado 2018B: {n} filas")

    up = st.file_uploader("subjects_2025.csv", type=["csv"], key="up2025")
    if up and st.button("Importar 2025"):
        n = import_subjects_2025(up.getvalue())
        st.success(f"Importado 2025: {n} filas")

    up = st.file_uploader("cr_activities.csv", type=["csv"], key="upcr")
    if up and st.button("Importar CR→CRE"):
        n = import_cr_activities(up.getvalue())
        st.success(f"Importado CR→CRE: {n} filas")

    st.divider()
    st.caption("Parámetros de cálculo")
    st.write(f"Plan 2018 total horas: {PLAN2018_TOTAL_HOURS}")
    st.write(f"Plan 2025 total horas: {PLAN2025_TOTAL_HOURS}")
    st.write(f"ACA requeridos: {ACA_TOTAL_REQUIRED}")
    st.write(f"Conversión fallback: 1 crédito → {CREDITS_TO_HOURS} hs")

    st.divider()
    st.subheader("Mantenimiento")

    st.caption(
        "Limpieza opcional: elimina selecciones/actividades de estudiantes que "
        "referencian códigos que ya no existen en los catálogos actuales."
    )

    confirm = st.checkbox("Entiendo que esto puede borrar selecciones huérfanas", value=False)

    if st.button("Ejecutar limpieza de selecciones huérfanas", disabled=not confirm):
        stats = cleanup_orphan_selections()
        st.success(
            "Limpieza completada. "
            f"StudentSelection(A): {stats['deleted_student_selection_A']}, "
            f"StudentSelection(B): {stats['deleted_student_selection_B']}, "
            f"CR completions: {stats['deleted_cr_activity_completions']}."
        )

    st.subheader("Transacciones de estudiantes (auditoría)")

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        q_user = st.text_input("Filtrar por usuario (user_id contiene)", value="")
    with col2:
        q_variant = st.selectbox("Variante", options=["(todas)", "A", "B"])
    with col3:
        q_type = st.selectbox("Tipo", options=["(todos)", "SAVE_SELECTION", "CALC"])

    limit = st.slider("Máximo de registros", min_value=50, max_value=2000, value=200, step=50)

    db = get_db()
    try:
        query = db.query(AuditEvent)

        if q_user.strip():
            query = query.filter(AuditEvent.user_id.ilike(f"%{q_user.strip()}%"))

        if q_variant != "(todas)":
            query = query.filter(AuditEvent.variant == q_variant)

        if q_type != "(todos)":
            query = query.filter(AuditEvent.event_type == q_type)

        rows = query.order_by(AuditEvent.ts.desc()).limit(limit).all()

        df = pd.DataFrame([{
            "ts": r.ts,
            "user_id": r.user_id,
            "variant": r.variant,
            "event_type": r.event_type,
            "payload": r.payload_json,
        } for r in rows])

    finally:
        db.close()

    if df.empty:
        st.info("No hay transacciones para los filtros seleccionados.")
    else:
        st.dataframe(df, use_container_width=True)

        st.caption("Tip: copiá un user_id y filtrá para ver el historial de ese estudiante.")

