from __future__ import annotations

import hmac
import os
import streamlit as st


def _get_admin_password() -> str | None:
    # 1) variable de entorno (ideal para Docker/servers)
    pwd = os.environ.get("TRANSICION_ADMIN_PASSWORD")
    if pwd:
        return pwd

    # 2) fallback: secrets (ideal para Community Cloud)
    # En Community Cloud lo cargás en Advanced settings.
    try:
        return st.secrets.get("TRANSICION_ADMIN_PASSWORD")
    except Exception:
        return None


def require_admin() -> bool:
    """Bloquea acceso si no hay login. Devuelve True si está autenticado."""
    if st.session_state.get("admin_ok"):
        return True

    expected = _get_admin_password()
    if not expected:
        st.error(
            "Admin deshabilitado: no está configurada la clave. "
            "Definí TRANSICION_ADMIN_PASSWORD como variable de entorno o secret."
        )
        st.stop()

    st.subheader("Acceso Administrador")
    pwd = st.text_input("Clave", type="password")

    if st.button("Ingresar", type="primary"):
        # comparación segura
        if hmac.compare_digest(pwd or "", expected):
            st.session_state["admin_ok"] = True
            st.rerun()
        else:
            st.error("Clave incorrecta.")

    st.stop()
