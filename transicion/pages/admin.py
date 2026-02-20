import pandas as pd
import streamlit as st
import os

from transicion.models import init_db, SessionLocal
from transicion.importer import (
    import_subjects_2018A,
    import_subjects_2018B,
    import_subjects_2025,
    import_cr_activities,
)
from transicion.models import Subject2018A, Subject2018B, Subject2025, CrActivity, AuditEvent
from transicion.persist import save_student_selection
from transicion.calculator import (
    run_calc, 
    PLAN2018_TOTAL_HOURS, 
    PLAN2025_TOTAL_HOURS, 
    ACA_TOTAL_REQUIRED, 
    CREDITS_TO_HOURS
)
from transicion.maintenance import cleanup_orphan_selections

def get_db():
    return SessionLocal()

def render_admin():
    init_db()
    
    # --- 1. SEGURIDAD Y AUTENTICACIÓN ---
    admin_password = st.secrets.get("TRANSICION_ADMIN_PASSWORD") or os.getenv("TRANSICION_ADMIN_PASSWORD")

    if not admin_password:
        st.error("🚫 **Configuración Incompleta:** No se ha definido la variable `TRANSICION_ADMIN_PASSWORD`.")
        st.info("Por favor, configúrala en los Secrets de Streamlit o en tu archivo .env")
        return

    if "admin_authenticated" not in st.session_state:
        st.session_state["admin_authenticated"] = False

    if not st.session_state["admin_authenticated"]:
        st.title("🔐 Acceso Administrativo")
        with st.form("login_admin"):
            password_input = st.text_input("Ingresá la contraseña maestra", type="password")
            if st.form_submit_button("Entrar"):
                if password_input == admin_password:
                    st.session_state["admin_authenticated"] = True
                    st.rerun()
                else:
                    st.error("Contraseña incorrecta")
        return

    # --- 2. INTERFAZ PRINCIPAL (AUTENTICADO) ---
    st.title("🛠️ Panel de Control Admin")
    
    with st.sidebar:
        st.success("Sesión: Administrador")
        if st.button("Cerrar Sesión"):
            st.session_state["admin_authenticated"] = False
            for key in ["step", "user_id", "nombre", "dni"]:
                if key in st.session_state: del st.session_state[key]
            st.rerun()

    tab_import, tab_audit, tab_maint = st.tabs(["📥 Importar Catálogos", "📋 Auditoría", "🧹 Mantenimiento"])

    # --- TAB 1: IMPORTACIÓN CON VALIDADOR DE HEADERS ---
    with tab_import:
        st.header("Actualización de Datos")
        st.caption("Subí los archivos CSV. El sistema validará que los encabezados sean correctos.")

        db = get_db()
        try:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("2018A", db.query(Subject2018A).count())
            c2.metric("2018B", db.query(Subject2018B).count())
            c3.metric("2025", db.query(Subject2025).count())
            c4.metric("Act. CR", db.query(CrActivity).count())
        finally:
            db.close()

        st.divider()

        col_a, col_b = st.columns(2)
        
        with col_a:
            # --- Bloque 2018A ---
            up_a = st.file_uploader("subjects_2018A.csv", type=["csv"], key="up2018a")
            if up_a and st.button("Importar 2018A", use_container_width=True):
                try:
                    n = import_subjects_2018A(up_a.getvalue())
                    st.success(f"✅ Importado 2018A: {n} filas")
                except ValueError as ve:
                    st.error(f"❌ Error de formato: {ve}")
                except Exception as e:
                    st.error(f"❌ Error inesperado: {e}")

            # --- Bloque 2025 ---
            up_25 = st.file_uploader("subjects_2025.csv", type=["csv"], key="up2025")
            if up_25 and st.button("Importar 2025", use_container_width=True):
                try:
                    n = import_subjects_2025(up_25.getvalue())
                    st.success(f"✅ Importado 2025: {n} filas")
                except ValueError as ve:
                    st.error(f"❌ Error de formato: {ve}")
                except Exception as e:
                    st.error(f"❌ Error inesperado: {e}")

        with col_b:
            # --- Bloque 2018B ---
            up_b = st.file_uploader("subjects_2018B.csv", type=["csv"], key="up2018b")
            if up_b and st.button("Importar 2018B", use_container_width=True):
                try:
                    n = import_subjects_2018B(up_b.getvalue())
                    st.success(f"✅ Importado 2018B: {n} filas")
                except ValueError as ve:
                    st.error(f"❌ Error de formato: {ve}")
                except Exception as e:
                    st.error(f"❌ Error inesperado: {e}")

            # --- Bloque CR ---
            up_cr = st.file_uploader("cr_activities.csv", type=["csv"], key="upcr")
            if up_cr and st.button("Importar CR→CRE", use_container_width=True):
                try:
                    n = import_cr_activities(up_cr.getvalue())
                    st.success(f"✅ Importado CR: {n} filas")
                except ValueError as ve:
                    st.error(f"❌ Error de formato: {ve}")
                except Exception as e:
                    st.error(f"❌ Error inesperado: {e}")

        with st.expander("⚙️ Ver constantes de cálculo actuales"):
            st.write(f"**Total Horas 2018:** {PLAN2018_TOTAL_HOURS}")
            st.write(f"**Total Horas 2025:** {PLAN2025_TOTAL_HOURS}")
            st.write(f"**ACA requeridos:** {ACA_TOTAL_REQUIRED}")
            st.write(f"**Conversión:** 1 crédito = {CREDITS_TO_HOURS} hs")

    # --- TAB 2: AUDITORÍA ---
    with tab_audit:
        st.header("Transacciones de Estudiantes")
        
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            q_user = st.text_input("Filtrar por nombre/DNI", value="")
        with c2:
            q_variant = st.selectbox("Variante", options=["(todas)", "A", "B"])
        with c3:
            q_type = st.selectbox("Evento", options=["(todos)", "SAVE_SELECTION", "CALC"])

        limit = st.slider("Registros a mostrar", 50, 1000, 200)

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
            
            if rows:
                df = pd.DataFrame([{
                    "Fecha": r.ts,
                    "Estudiante": r.user_id,
                    "Plan": r.variant,
                    "Acción": r.event_type,
                    "Detalle": r.payload_json,
                } for r in rows])
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No hay registros que coincidan con los filtros.")
        finally:
            db.close()

    # --- TAB 3: MANTENIMIENTO ---
    with tab_maint:
        st.header("Limpieza de Base de Datos")
        st.warning("Estas acciones son irreversibles. Usar con precaución.")
        
        st.write("""
            **Limpieza de Huérfanos:** Elimina los registros de materias aprobadas de estudiantes 
            que referencian a códigos que ya no existen en los catálogos actuales (después de una re-importación).
        """)
        
        confirm = st.checkbox("Confirmo que deseo realizar tareas de mantenimiento")
        
        if st.button("🔥 Ejecutar limpieza de huérfanos", disabled=not confirm):
            with st.spinner("Limpiando..."):
                stats = cleanup_orphan_selections()
                st.success(f"""
                    **Mantenimiento Exitoso:**
                    - Selecciones Plan A borradas: {stats['deleted_student_selection_A']}
                    - Selecciones Plan B borradas: {stats['deleted_student_selection_B']}
                    - Actividades CR borradas: {stats['deleted_cr_activity_completions']}
                """)