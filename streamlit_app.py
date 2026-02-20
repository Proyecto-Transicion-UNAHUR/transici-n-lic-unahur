import streamlit as st
from transicion.pages.student import render_student
from transicion.pages.admin import render_admin
from transicion.auth import require_admin
from dotenv import load_dotenv
load_dotenv() # Esto carga el archivo .env en el sistema

# Configuración global de la interfaz
st.set_page_config(page_title="Transición Plan 2018/2022 → 2025", layout="wide")

# Función para renderizar la vista del estudiante (pública)
def page_student():
    render_student()

# Función para renderizar la vista administrativa (protegida por login)
def page_admin():
    require_admin() # Verifica si el usuario tiene permisos
    render_admin()

# Definición del menú de navegación lateral
pg = st.navigation({
    "Estudiante": [
        st.Page(page_student, title="Analizar transición", icon="🎓"),
    ],
    "Administración": [
        st.Page(page_admin, title="Admin", icon="🔒"),
    ],
})

# Ejecución de la navegación
pg.run()

