from __future__ import annotations

from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def build_pdf_bytes(result: dict) -> bytes:
    """Generate a simple PDF report (in memory) using ReportLab.

    This keeps deployment simple (no WeasyPrint system dependencies).
    """
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4

    x = 50
    y = height - 50

    def line(text: str, dy: int = 16, size: int = 11, bold: bool = False):
        nonlocal y
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        c.drawString(x, y, text)
        y -= dy
        if y < 80:
            c.showPage()
            y = height - 50

    # Header
    line("Informe de transición Plan 2018 → Plan 2025", dy=22, size=14, bold=True)
    line(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    line(f"Estudiante: {result.get('user_id','')}")
    line(f"Modo: {result.get('variant','')}")
    line(" ")

    # Progress
    hrs2018 = result.get("hrs_2018", {})
    hrs2025 = result.get("hrs_2025", {})
    line("Avance", dy=20, size=12, bold=True)
    line(f"Plan 2018: {hrs2018.get('got',0)} / {hrs2018.get('total',0)} horas")
    line(f"Plan 2025: {hrs2025.get('got',0)} / {hrs2025.get('total',0)} horas")

    aca = result.get("aca_credits", 0)
    aca_req = result.get("aca_required", 30)
    line(f"ACA (CRE): {aca} / {aca_req}")
    line(f"  - Por materias: {result.get('aca_from_subjects',0)}")
    line(f"  - Por actividades CR→CRE: {result.get('aca_from_cr',0)}")
    line(" ")

    # Equivalences
    line("Materias aprobadas en Plan 2025 (por equivalencia)", dy=20, size=12, bold=True)
    for item in result.get("equivalences_2025", []):
        code = item.get("code", "")
        name = item.get("name", "")
        hours = item.get("hours_total", "")
        line(f"- {code} — {name} ({hours} hs)", dy=14, size=10)

    # Partials
    partials = result.get("partials", []) or []
    if partials:
        line(" ")
        line("Casos parciales (MERGE)", dy=20, size=12, bold=True)
        for p in partials:
            dst = ", ".join(p.get("dst", []))
            have = ", ".join(p.get("have", []))
            missing = ", ".join(p.get("missing", []))
            aca_g = p.get("aca_granted", 0)
            mode = p.get("mode", "")
            line(f"- Destino: {dst}", dy=14, size=10)
            line(f"  Aprobadas: {have}", dy=14, size=10)
            line(f"  Faltan: {missing}", dy=14, size=10)
            line(f"  ACA reconocidos: {aca_g} (modo: {mode})", dy=14, size=10)

    c.showPage()
    c.save()
    return buf.getvalue()
