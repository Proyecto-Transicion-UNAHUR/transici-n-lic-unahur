import streamlit as st

from transicion.pages.student import render_student
from transicion.pages.admin import render_admin
from transicion.auth import require_admin

st.set_page_config(page_title="Transición Plan 2018 → 2025", layout="wide")

# Definimos "páginas" como callables
def page_student():
    render_student()

def page_admin():
    require_admin()
    render_admin()

pg = st.navigation({
    "Estudiante": [
        st.Page(page_student, title="Analizar transición", icon="🎓"),
    ],
    "Administración": [
        st.Page(page_admin, title="Admin", icon="🔒"),
    ],
})

pg.run()
