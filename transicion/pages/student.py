import streamlit as st
from transicion.models import init_db, SessionLocal
import pandas as pd
from transicion.persist import save_student_selection
from transicion.calculator import run_calc
from transicion.pdf_report import build_pdf_bytes
from transicion.models import Subject2018A, Subject2018B, CrActivity

def get_db():
    return SessionLocal()

# --- FUNCIÓN DE LIMPIEZA CORREGIDA ---
def logout_reset():
    # Eliminamos todo el estado
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    # Forzamos el rerun para que se reinicialice todo en la primera línea de render_student
    st.rerun()

def render_student():
    init_db()
    
    # --- INICIALIZACIÓN DE ESTADOS (Mantenlo aquí arriba) ---
    # Esto evita el KeyError: 'step' porque se ejecuta antes que cualquier lógica
    if "step" not in st.session_state:
        st.session_state["step"] = 1
    if "nombre" not in st.session_state:
        st.session_state["nombre"] = ""
    if "dni" not in st.session_state:
        st.session_state["dni"] = ""
    if "variant" not in st.session_state:
        st.session_state["variant"] = "A"
    if "user_id" not in st.session_state:
        st.session_state["user_id"] = ""

    # Sidebar con opción de reset
    with st.sidebar:
        st.write("⚙️ Opciones de sesión")
        if st.button("🔌 Cerrar Sesión / Reset"):
            logout_reset()

    st.title("🚀 Transición Plan 2018/2022 → Plan 2025")

    # --- STEP 1: DATOS DEL ESTUDIANTE ---
    if st.session_state["step"] == 1:
        st.subheader("¡Hola! Contanos quién sos")
        c1, c2, c3 = st.columns([2, 1, 2])
        with c1:
            st.session_state["nombre"] = st.text_input("Nombre y apellido", st.session_state["nombre"])
        with c2:
            st.session_state["dni"] = st.text_input("DNI", st.session_state["dni"])
        with c3:
            st.session_state["variant"] = st.radio(
                "Tu plan actual", 
                options=["A", "B"], 
                format_func=lambda x: "Tecnicatura 2018 (Original)" if x == "A" else "Tecnicaturas 2022 (Nuevas)",
                index=0 if st.session_state["variant"] == "A" else 1
            )
        
        if st.button("Empezar análisis →"):
            nombre = (st.session_state["nombre"] or "").strip()
            dni = (st.session_state["dni"] or "").strip()
            st.session_state["user_id"] = f"{nombre}|{dni}" if (nombre or dni) else "alumno_temp"
            st.session_state["step"] = 2
            st.rerun()

    # --- STEP 2: SELECCIÓN EN CASCADA ---
    elif st.session_state["step"] == 2:
        user_id = st.session_state["user_id"]
        variant = st.session_state["variant"]

        db = get_db()
        try:
            subjects = db.query(Subject2018B).all() if variant == "B" else db.query(Subject2018A).all()
            acts = db.query(CrActivity).all()
        finally:
            db.close()

        st.subheader("✅ Marcá tus materias aprobadas")

        with st.form("form_cascada"):
            current_selection = []

            def render_checkbox_group(title, keywords, block_id):
                with st.expander(title):
                    filtered = [s for s in subjects if any(x.lower() in s.name.lower() for x in keywords)]
                    if not filtered:
                        st.caption("No se encontraron materias en este bloque.")
                    for s in filtered:
                        unique_key = f"s_{block_id}_{s.code}" 
                        if st.checkbox(f"[{s.code}] {s.name}", key=unique_key):
                            current_selection.append(s.code)

            # Bloques de materias
            render_checkbox_group("1 - Materias Comunes", ["Inglés", "UNAHUR", "Entornos", "Cultura"], "B1")
            render_checkbox_group("2 - Compartidas Informática", ["Matemática", "Lógica", "Organización", "Estructurada"], "B2")
            render_checkbox_group("3 - Redes", ["Comunicación", "Operaciones", "Redes"], "B3")
            render_checkbox_group("4 - Videojuegos", ["Videojuegos", "Arte Digital", "Diseño Conceptual"], "B4")
            render_checkbox_group("5 - Inteligencia Artificial", ["IA", "Datos", "Neuronales", "Aprendizaje Automático"], "B5")
            render_checkbox_group("6 - Licenciatura Anterior", ["Arquitectura", "Distribuidos", "Tesina"], "B6")
            render_checkbox_group("7 - Programación", ["Objetos", "Estructuras", "Concurrente", "Funcional"], "B7")
            render_checkbox_group("8 - Específicas 2025", ["Seguridad", "PPS", "Algoritmos", "Computabilidad"], "B8")
            render_checkbox_group("9 - Optativas / Electivas", ["Electiva", "Optativa"], "B9")

            with st.expander("10 - Actividades ACA/CR"):
                current_acts = []
                for a in acts:
                    if st.checkbox(f"[{a.code}] {a.description}", key=f"act_{a.code}"):
                        current_acts.append(a.code)

            st.divider()
            c1, c2 = st.columns(2)
            with c2:
                submit = st.form_submit_button("🔥 Ver mis resultados", use_container_width=True)
            with c1:
                back = st.form_submit_button("Atrás", use_container_width=True)

            if submit:
                st.session_state["selected_codes"] = list(set(current_selection))
                st.session_state["selected_acts"] = current_acts
                save_student_selection(user_id, variant, st.session_state["selected_codes"], current_acts)
                st.session_state["step"] = 3
                st.rerun()
            
            if back:
                st.session_state["step"] = 1
                st.rerun()

    # --- STEP 3: DASHBOARD ---
    elif st.session_state["step"] == 3:
        user_id = st.session_state["user_id"]
        variant = st.session_state["variant"]
        
        db = get_db()
        try:
            result = run_calc(db, user_id, variant)
        finally:
            db.close()
            
        st.success(f"### ¡Análisis completado!")
        
        # Métrica de progreso
        HORAS_REQ_ANALISTA = 1440 
        hrs_got = result["hrs_2018"]["got"]
        porc_analista = min(100.0, (hrs_got / HORAS_REQ_ANALISTA) * 100)
        
        st.write(f"**Progreso hacia Analista:** {porc_analista:.1f}%")
        st.progress(porc_analista / 100)

        # Dashboard Visual
        st.divider()
        m1, m2, m3 = st.columns(3)
        m1.metric("Horas", f"{hrs_got} hs")
        m2.metric("Materias 2025", len(result["equivalences_2025"]))
        m3.metric("Créditos ACA", f"{result['aca_credits']}")

        # Gráfico
        chart_data = pd.DataFrame({
            "Plan": ["Viejo", "Nuevo"],
            "Avance %": [
                (hrs_got / max(1, result['hrs_2018']['total'])) * 100,
                (result['hrs_2025']['got'] / max(1, result['hrs_2025']['total'])) * 100
            ]
        }).set_index("Plan")
        st.bar_chart(chart_data, horizontal=True, height=200)

        with st.expander("Ver materias equivalentes"):
            st.dataframe(pd.DataFrame(result["equivalences_2025"]), use_container_width=True)

        st.divider()
        pdf_bytes = build_pdf_bytes(result)
        st.download_button("📥 Descargar PDF", data=pdf_bytes, file_name="analisis.pdf", use_container_width=True)

        if st.button("🔄 Nueva consulta"):
            st.session_state["step"] = 1
            st.rerun()