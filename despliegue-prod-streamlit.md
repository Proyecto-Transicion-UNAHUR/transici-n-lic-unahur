1) Subir el proyecto a GitHub
1.1. Crear repo
En GitHub: “New repository”
Elegí nombre, por ejemplo: transicion-lic-streamlit
1.2. Subir tu código (comandos típicos)
En la carpeta del proyecto:
git init
git add .
git commit -m "Primera versión: transición estudiante + admin con clave"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/transicion-lic-streamlit.git
git push -u origin main
2) Publicar en Streamlit Community Cloud
2.1. Entrar y conectar GitHub
Ir a la plataforma de Streamlit Community Cloud (desde la documentación de “Deploy your app”).
Conectar tu cuenta de GitHub (autorización). Esto es necesario para que Streamlit lea tu repo.
2.2. Crear la app
En “Deploy an app” (o “New app”):
Repository: tu repo
Branch: main
Main file path: streamlit_app.py
App URL: elegí el subdominio (p. ej. transicion-lic)
Streamlit construye el entorno e instala dependencias desde requirements.txt.
3) Configurar la clave de Admin (por “variable de entorno / secrets”)
En Community Cloud, el modo estándar es cargar secretos en la UI (“Secrets management”) y accederlos con st.secrets.
3.1. En la UI de Streamlit Cloud
Abrí tu app en el dashboard
Entrá a Settings / Secrets
Pegá:
TRANSICION_ADMIN_PASSWORD="una_clave_fuerte"
3.2. En tu código
Tu helper debe leer primero os.environ y si no existe, st.secrets (así funciona local y cloud).
Esto es compatible con el enfoque recomendado de Streamlit para secretos.
4) Ciclo de actualización (push → deploy)
4.1. Flujo típico
Editás código localmente
Probás local
Hacés commit + push
Streamlit Cloud detecta el cambio y redeploya
Comandos:
git add .
git commit -m "Cambio X"
git push
En la mayoría de los casos, el despliegue es automático.
4.2. Si no se actualiza (casos comunes)
A veces la app no refleja cambios inmediatamente y requiere “reboot” o revisar conexión GitHub. Es un issue reportado en Community Cloud; normalmente se resuelve desde el panel de la app (“Reboot” / “Rerun”) o revisando la conexión al repo.
Checklist rápido:
¿Hiciste push al branch correcto (main)?
¿El repo es privado y Streamlit perdió permisos? (reconectar GitHub en Cloud)
¿Cambiaste dependencias? (a veces conviene “Reboot” para forzar rebuild)
5) Elegir versión de Python (muy importante)
En Community Cloud no se usa runtime.txt para fijar Python. Se selecciona en la UI de la app (settings). Esto ha cambiado respecto a prácticas antiguas.
Recomendación práctica para evitar sorpresas:
usar Python 3.11 o 3.12 (según lo que te ofrezca la UI) y mantenerlo estable.