import streamlit as st
from transicion.models import init_db, SessionLocal
import pandas as pd
from transicion.persist import save_student_selection
from transicion.calculator import run_calc, PLAN2018_TOTAL_HOURS, PLAN2025_TOTAL_HOURS, ACA_TOTAL_REQUIRED, CREDITS_TO_HOURS
from transicion.pdf_report import build_pdf_bytes
from transicion.models import AuditEvent
from transicion.models import Subject2018A, Subject2018B, Subject2025, CrActivity

# y tus imports actuales (load rules, run calc, pdf, etc.)

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


def render_student():
    init_db()
    # ✅ Inicialización por sesión (clave para multi-sesión)
    st.session_state.setdefault("step", 1)
    st.session_state.setdefault("nombre", "")
    st.session_state.setdefault("dni", "")
    st.session_state.setdefault("variant", "A")   # A o B

    # selections (según cómo lo implementaste)
    st.session_state.setdefault("subject_codes", [])
    st.session_state.setdefault("activity_codes", [])

    st.title("Transición Plan 2018 → Plan 2025")

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
