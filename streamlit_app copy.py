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


st.set_page_config(page_title="Transición Plan 2018 → 2025", layout="wide")
init_db()


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


st.title("Transición Plan 2018 → Plan 2025")
tab_user, tab_admin = st.tabs(["Consulta de estudiante", "Administración"])


# --- Sidebar Admin ---

import pandas as pd
from transicion.models import AuditEvent

with tab_admin:
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


with tab_user:
    # --- Step 1: identity ---
    if st.session_state["step"] == 1:
        st.subheader("Datos del/de la estudiante")

        c1, c2, c3 = st.columns([2, 1, 2])
        with c1:
            st.session_state["nombre"] = st.text_input("Nombre y apellido", st.session_state["nombre"])
        with c2:
            st.session_state["dni"] = st.text_input("DNI", st.session_state["dni"])
        with c3:
            st.session_state["variant"] = st.radio(
                "Modo de cursada",
                options=["A", "B"],
                format_func=lambda x: "Tecnicatura 2018 (sin división)" if x == "A" else "Tecnicaturas 2022 (con división)",
                index=0 if st.session_state["variant"] == "A" else 1,
            )

        if st.button("Continuar"):
            nombre = (st.session_state["nombre"] or "").strip()
            dni = (st.session_state["dni"] or "").strip()
            st.session_state["user_id"] = f"{nombre}|{dni}" if (nombre or dni) else "alumno123"
            st.session_state["step"] = 2
            st.rerun()


    # --- Step 2: selections ---
    if st.session_state["step"] == 2:
        user_id = st.session_state["user_id"]
        variant = st.session_state["variant"]

        st.subheader("Selección de materias aprobadas (Plan 2018)")
        st.caption(f"Estudiante: {user_id} | Modo: {variant}")

        db = get_db()
        try:
            if variant == "B":
                subjects = db.query(Subject2018B).order_by(Subject2018B.code).all()
            else:
                subjects = db.query(Subject2018A).order_by(Subject2018A.code).all()
        finally:
            db.close()

        if not subjects:
            st.warning("No hay materias cargadas para este modo. Importá el CSV correspondiente desde la barra lateral.")

        df = pd.DataFrame([{"code": s.code, "name": s.name} for s in subjects])
        options = df["code"].tolist() if not df.empty else []

        selected_codes = st.multiselect(
            "Marcá las materias aprobadas",
            options=options,
            format_func=lambda c: f"{c} — {df.loc[df.code == c, 'name'].values[0]}" if not df.empty else c,
        )

        selected_acts = []
        if variant == "B":
            st.subheader("Actividades CR (sistema anterior) → ACA (CRE)")
            db = get_db()
            try:
                acts = db.query(CrActivity).order_by(CrActivity.code).all()
            finally:
                db.close()

            if not acts:
                st.info("No hay actividades CR cargadas. Importá cr_activities.csv desde la barra lateral si aplica.")
            else:
                df_a = pd.DataFrame([
                    {
                        "code": a.code,
                        "description": a.description,
                        "cr": a.cr_value,
                        "cre": a.cre_value,
                    }
                    for a in acts
                ])

                selected_acts = st.multiselect(
                    "Marcá las actividades completadas",
                    options=df_a["code"].tolist(),
                    format_func=lambda c: (
                        f"{c} — {df_a.loc[df_a.code == c, 'description'].values[0]} "
                        f"({df_a.loc[df_a.code == c, 'cr'].values[0]} CR → {df_a.loc[df_a.code == c, 'cre'].values[0]} ACA)"
                    ),
                )

        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("Volver"):
                st.session_state["step"] = 1
                st.rerun()
        with c2:
            if st.button("Calcular transición"):
                save_student_selection(user_id, variant, selected_codes, selected_acts)
                st.session_state["step"] = 3
                st.rerun()


    # --- Step 3: results ---
    if st.session_state["step"] == 3:
        user_id = st.session_state["user_id"]
        variant = st.session_state["variant"]

        db = get_db()
        try:
            result = run_calc(db, user_id, variant)

        finally:
            db.close()

        st.subheader("Resultados")

        # Plan 2018 progress
        hrs2018 = result["hrs_2018"]
        p2018 = hrs2018["got"] / max(1, hrs2018["total"])
        st.write(f"Plan 2018: {hrs2018['got']} / {hrs2018['total']} horas")
        st.progress(min(1.0, float(p2018)))

        # ACA summary
        st.write(
            f"ACA (CRE): {result['aca_credits']} / {result['aca_required']} "
            f"(materias: {result.get('aca_from_subjects',0)}, CR→CRE: {result.get('aca_from_cr',0)})"
        )

        # Plan 2025 progress (hours + ACA converted to units)
        total_2025_units = result["hrs_2025"]["total"] + result["aca_required"] * 25
        got_2025_units = result["hrs_2025"]["got"] + result["aca_credits"] * 25
        p2025 = got_2025_units / max(1, total_2025_units)
        st.write(f"Plan 2025: {result['hrs_2025']['got']} / {result['hrs_2025']['total']} horas (+ ACA)")
        st.progress(min(1.0, float(p2025)))

        st.markdown("### Materias equivalentes en Plan 2025")
        st.dataframe(pd.DataFrame(result["equivalences_2025"]))

        if result.get("partials"):
            st.markdown("### Casos parciales (MERGE)")
            st.dataframe(pd.DataFrame(result["partials"]))

        pdf_bytes = build_pdf_bytes(result)
        st.download_button(
            "Descargar informe PDF",
            data=pdf_bytes,
            file_name=f"transicion_{user_id.replace('|','_')}.pdf",
            mime="application/pdf",
        )

        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("Nueva consulta"):
                st.session_state["step"] = 1
                st.rerun()
        with c2:
            if st.button("Volver a selección"):
                st.session_state["step"] = 2
                st.rerun()
