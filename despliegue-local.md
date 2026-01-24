
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export TRANSICION_ADMIN_PASSWORD="clave-fuerte"  // 1234 para pruebas

python -m streamlit run streamlit_app.py --server.port 8502

