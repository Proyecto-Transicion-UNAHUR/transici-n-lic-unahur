## 0. Inicio LOCAL
source .venv/bin/activate
python -m streamlit run streamlit_app.py --server.port 8502

## 1. Transicion - Contenido de la carpeta

models.py
Tablas: subjects_2018A, subjects_2018B, subjects_2025, student_selection, cr_activities, cr_activity_completions.
DB path absoluto y estable: data/transicion.db.
rules_loader.py
Carga mapping_rules_<variant>.yaml si existe; si no, usa mapping_rules.yaml.
calculator.py
Aplica reglas DIRECT, SPLIT_1toN, MERGE_Nto1 (con ACA parciales) y ACA_ONLY; suma CR→CRE; cap a 30 ACA.
importer.py
Importa catálogos desde bytes (ideal para st.file_uploader).
persist.py
Guarda selección de materias y actividades CR del estudiante.
pdf_report.py
PDF simple en memoria con ReportLab.
maintenance.py
Elimina selecciones huérfanas en el caso que se importen nuevamente los catálogos y se cambien códigos. Útil mientras se están haciendo pruebas de funcionamiento.

## 2. Administración

2.1. Módulo Admin (barra lateral)
El módulo Admin (ubicado en la barra lateral izquierda) permite:
Ver el estado de carga de catálogos (conteo de filas).
Importar o reimportar catálogos desde CSV.
Ejecutar tareas de mantenimiento (limpieza).
Este módulo está pensado para usuarios con rol administrativo (equipo de gestión / soporte).
2.2. Importación de catálogos (CSV)
Catálogos disponibles
Materias Plan 2018A (subjects_2018A.csv)
Materias Plan 2018B (subjects_2018B.csv)
Materias Plan 2025 (subjects_2025.csv)
Actividades CR → CRE (ACA) (cr_activities.csv)
Política de importación: “reemplazar catálogo”
Al importar cualquiera de los CSV de catálogos, el sistema aplica una estrategia “clear-and-reload”:
Se borran todas las filas existentes del catálogo correspondiente.
Se cargan todas las filas del CSV importado.
Se confirma la operación y se informa cuántas filas se cargaron.
Esto evita:
Duplicación de materias/actividades.
Mezclas de versiones del plan.
Inconsistencias por cambios de nombre/créditos/horas.
Importante: las selecciones de estudiantes no se borran al importar catálogos
La importación de catálogos no modifica:
student_selection (materias seleccionadas por estudiante)
cr_activity_completions (actividades CR marcadas por estudiante)
Esto preserva la información de usuarios aunque se actualicen catálogos.
2.3. Consecuencia esperada: códigos “huérfanos”
Si un catálogo se reimporta con cambios (por ejemplo, se elimina o renombra un código), puede ocurrir que un estudiante tenga una selección histórica referenciando un código que ya no existe en el catálogo actual.
Esto puede producir:
Que ese código no aparezca en la pantalla de selección (porque se listan materias desde el catálogo vigente).
Que en resultados el nombre/hora del código no se pueda resolver desde el catálogo.
Para resolverlo, el sistema ofrece una limpieza opcional (ver siguiente sección).
2.4. Mantenimiento: Limpieza de selecciones huérfanas
El Admin incluye la acción “Ejecutar limpieza de selecciones huérfanas”.
Qué hace
Elimina registros de estudiantes que referencian códigos inexistentes en el catálogo actual:
StudentSelection (materias aprobadas del plan 2018):
Variante A: borra selecciones cuyo subject_code ya no exista en subjects_2018A.
Variante B: borra selecciones cuyo subject_code ya no exista en subjects_2018B.
CrActivityCompletion (actividades CR):
Borra completitudes cuyo activity_code ya no exista en cr_activities.
Qué no hace
No modifica ni borra catálogos.
No altera reglas de transición (mapping_rules*.yaml).
No recalcula resultados; solo limpia datos inconsistentes.
Confirmación
Por seguridad, la interfaz requiere marcar una confirmación antes de ejecutar la limpieza. Al finalizar, informa cuántos registros fueron eliminados por cada tabla.
2.5. Recomendación operativa
En operación habitual:
Importar/actualizar catálogos (si hubo cambios).
Ejecutar la limpieza solo si se modificaron códigos y se detectan inconsistencias o selecciones que ya no aparecen en UI.
Validar con un usuario de prueba (consulta normal) que los resultados sean consistentes.


## Reglas

# NOTAS sobre reglas de configuración
# Uso del archivo de configuracion

1. Estructura general de una regla
Cada entrada en mapping_rules.yaml es un diccionario con esta estructura general:
- type: DIRECT | SPLIT_1toN | MERGE_Nto1 | ACA_ONLY
  src_2018_codes: [ ... ]    # códigos del plan 2018
  dst_2025_codes: [ ... ]    # códigos del plan 2025 (si aplica)
  aca_on_partial: N          # ACA a otorgar por aprobación parcial (solo MERGE_Nto1)
  aca_partial_mode: per_source | per_rule
  aca_credits: N             # ACA a otorgar en reglas ACA_ONLY
  comment: "texto libre"
No todos los campos se usan en todos los tipos. Abajo va el detalle.
2. Tipos de regla y su comportamiento
2.1. DIRECT
Caso típico: equivalencias “limpias” entre materias del 2018 y el 2025.
Uso principal:
“Si el/la estudiante aprobó TODAS las materias de src_2018_codes, se le aprueban TODAS las de dst_2025_codes”.
Campos usados:
type: "DIRECT"
src_2018_codes: lista de materias del plan 2018.
dst_2025_codes: lista de materias equivalentes del plan 2025.
comment (opcional): explicación.
Ejemplos:
1 a 1:
- type: DIRECT
  src_2018_codes: ["LI101"]
  dst_2025_codes: ["LI1001"]
  comment: "Introducción a la informática → Fundamentos de informática"
2 a 2 (se requieren ambas):
- type: DIRECT
  src_2018_codes: ["LI201", "LI202"]
  dst_2025_codes: ["LI2001", "LI2002"]
  comment: "Bloque de programación I+II"
2.2. SPLIT_1toN
Caso típico: una materia vieja se “divide” en dos o más del nuevo plan.
Uso principal:
“Si la materia de origen está aprobada, se aprueban varias del 2025”.
Campos usados:
type: "SPLIT_1toN"
src_2018_codes: debe tener una materia (la de 2018).
dst_2025_codes: lista de materias del 2025 que se otorgan.
comment (opcional).
Comportamiento:
Si src_2018_codes[0] está en el conjunto de materias aprobadas del 2018 → se marcan como aprobadas todas las dst_2025_codes.
Ejemplo:
- type: SPLIT_1toN
  src_2018_codes: ["LI150"]
  dst_2025_codes: ["LI1501", "LI1502"]
  comment: "Materia anual antigua se separa en dos cuatrimestrales"
2.3. MERGE_Nto1
Caso típico: varias materias del 2018 se “fusionan” en una sola materia del 2025.
Uso principal:
Si el/la estudiante tiene todas las materias de src_2018_codes aprobadas → se aprueban las dst_2025_codes.
Si tiene una parte, se pueden otorgar ACA parciales (según cómo se configure).
Campos usados:
type: "MERGE_Nto1"
src_2018_codes: lista de materias requeridas del 2018.
dst_2025_codes: normalmente una materia del 2025, pero puede ser más de una si lo necesitás.
aca_on_partial (opcional): cuántos ACA se otorgan si hay aprobación parcial.
aca_partial_mode (opcional):
"per_source" → se aplica por cada materia de origen aprobada.
"per_rule" → se aplica una sola vez por regla, aunque el/la estudiante tenga 1, 2, … (pero menos que todas).
comment (opcional).
Comportamiento resumido:
Sea N = len(src_2018_codes) y k = número de materias aprobadas entre ellas:
Si k == N → se aprueban las dst_2025_codes.
Si 1 ≤ k < N:
Si aca_on_partial está definido:
Si aca_partial_mode == "per_source" → ACA extra = k * aca_on_partial.
Si aca_partial_mode == "per_rule" → ACA extra = aca_on_partial.
Si aca_on_partial no está definido → no se generan ACA parciales.
Ejemplos:
3 a 1, otorgando 3 ACA por cada materia parcial aprobada:
- type: MERGE_Nto1
  src_2018_codes: ["LI301", "LI302", "LI303"]
  dst_2025_codes: ["LI3001"]
  aca_on_partial: 3
  aca_partial_mode: per_source
  comment: "Conjunto de tres talleres que forman una materia integrada"
2 a 1, otorgando 5 ACA una sola vez si falta alguna:
- type: MERGE_Nto1
  src_2018_codes: ["LI210", "LI211"]
  dst_2025_codes: ["LI2100"]
  aca_on_partial: 5
  aca_partial_mode: per_rule
  comment: "Si tiene 1/2 talleres se reconocen 5 ACA, si tiene 2/2 se le da la materia completa"
2.4. ACA_ONLY
Caso típico: reconocer solo ACA por materias del plan 2018, sin equivalencia directa a materias del 2025.
Uso principal:
“Si el/la estudiante aprobó alguna de estas materias del 2018, se otorgan ACA, pero no se aprueba ninguna materia nueva”.
Campos usados:
type: "ACA_ONLY"
src_2018_codes: lista de materias del 2018 que habilitan el reconocimiento.
aca_credits: cantidad de ACA que se suman si se cumple la condición.
comment (opcional).
dst_2025_codes se puede omitir o dejar vacío (no se usan para equivalencia).
Comportamiento concreto:
Si al menos una materia de src_2018_codes está aprobada → se suman aca_credits al total de ACA.
Esto se acumula con lo que venga de MERGE_Nto1 y con las actividades CR→CRE, siempre respetando el tope global de 30 ACA.
Ejemplo:
- type: ACA_ONLY
  src_2018_codes: ["LI999"]
  aca_credits: 4
  comment: "Seminario optativo antiguo reconocido solo como ACA"
3. Otras posibilidades de configuración
3.1. Variantes por plan/tipo de cursada (A/B)
En el código también habilitamos la carga por variante:
mapping_rules.yaml → reglas generales.
mapping_rules_A.yaml → reglas específicas para el modo A (Tecnicatura 2018).
mapping_rules_B.yaml → reglas específicas para el modo B (Tecnicaturas 2022).
La función load_rules(variant) busca:
Si existe mapping_rules_<variant>.yaml (por ejemplo mapping_rules_B.yaml), lo usa.
Si no, cae al mapping_rules.yaml general.
Esto te permite:
Tener un solo archivo para todo, o
Tener archivos separados si la transición A y B son suficientemente distintas.
4. Resumen ultra corto
En mapping_rules.yaml podés definir:
DIRECT
Mapping limpio: si tiene estas materias del 2018 → se aprueban estas del 2025.
SPLIT_1toN
Una materia antigua se “desdobla” en varias nuevas.
MERGE_Nto1
Varias materias viejas se fusionan en una nueva, con:
equivalencia completa si están todas,
ACA parciales según aca_on_partial y aca_partial_mode si tiene solo algunas.
ACA_ONLY
Ciertas materias viejas solo generan ACA (sin equivalencia directa de materia).
Y todo esto se combina con:
Cálculo de horas plan 2018,
Cálculo de horas y materias plan 2025,
ACA aportados por materias,
ACA aportados por actividades CR→CRE,
Tope global de 30 ACA.