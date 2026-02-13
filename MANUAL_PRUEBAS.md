📘 Guía de Simulación de Transición - Plan 2025
Este documento detalla los pasos para validar la lógica de equivalencias y la acreditación de créditos ACA diseñada para la Licenciatura en Informática de la UNAHUR.

🚀 Inicio del Sistema
Abra la terminal en la carpeta raíz del proyecto (C:\Users\transici-n-lic-unahur).

Asegúrese de que el entorno virtual esté activo (.venv).

Ejecute el comando: streamlit run streamlit_app.py.

🧪 Casos de Validación Estratégica
Escenario 1: Equivalencia Directa
Objetivo: Verificar que materias sin cambios se reconozcan automáticamente.

Materia a tildar: 753 (Programación con Objetos I).

Resultado: En el panel y el PDF, la materia 753 figura como Aprobada con 96 hs.

Escenario 2: Desglose por Contenidos (Split)
Objetivo: Validar que una materia antigua se divida en dos nuevas.

Materia a tildar: 767 (Introducción a la Programación).

Resultado: El sistema otorga automáticamente las materias 789 (64 hs) y 792 (96 hs).

Escenario 3: Lógica de Fusión y Créditos ACA (Crucial)
Objetivo: Demostrar que el alumno no pierde su esfuerzo ante cambios curriculares.

Acción: Tilde únicamente 761 (Programación Funcional).

Resultado:

La materia LI2 permanecerá Pendiente.

Se asignan 3 créditos ACA (visibles en el apartado ACA del informe).

Escenario 4: Acreditación Directa ACA
Objetivo: Validar el fondo de créditos complementarios.

Materia a tildar: ING1 (Inglés I).

Resultado: Suma 3 créditos ACA directos al contador del estudiante (ACA: 3/30).

Escenario 5: Validación de Reporte Formal
Acción: Completar datos de estudiante (ej. Martín Maldonado) y generar PDF.

Resultado: Emisión de un documento con fecha, avance en horas de ambos planes y lista detallada de equivalencias.

🛠️ Notas de Configuración y Mantenimiento
Reglas: Centralizadas en data/mapping_rules.yaml.

Base de Datos: Los planes se cargan desde data/subjects_2018A.csv, data/subjects_2018B.csv y data/subjects_2025.csv.

Dependencias: El sistema requiere streamlit, pandas, sqlalchemy, pyyaml y reportlab.
