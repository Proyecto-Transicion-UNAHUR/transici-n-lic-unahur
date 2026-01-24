Manual de Usuario
Aplicación de Análisis de Transición Curricular – Licenciatura en Informática
1. Objetivo de la aplicación
La aplicación tiene como objetivo permitir a estudiantes de la Licenciatura en Informática:
Analizar su situación académica frente al cambio del Plan 2018 al Plan 2025.
Visualizar equivalencias automáticas entre materias.
Identificar créditos ACA (CRE) obtenidos parcial o totalmente.
Conocer el avance porcentual en ambos planes.
Obtener un informe claro para la toma de decisiones académicas.
La herramienta también incluye un módulo administrativo para gestión de catálogos, actividades y auditoría.
2. Flujo de uso para estudiantes
2.1. Identificación inicial
Al ingresar a la aplicación, el estudiante debe completar:
Nombre y Apellido
DNI
Modalidad cursada del Plan 2018:
A) Tecnicatura 2018 (sin división de materias)
B) Tecnicaturas 2022 (con división de materias)
Esta selección define el conjunto de materias que se presentará para marcar como aprobadas.
2.2. Selección de materias aprobadas (Plan 2018)
Según la modalidad elegida:
Se muestra el listado correspondiente de materias:
subjects_2018A o subjects_2018B
El estudiante marca las materias que ya tiene aprobadas.
Estas selecciones representan el punto de partida para el cálculo de equivalencias.
2.3. Actividades CR (solo modalidad B)
Para quienes cursaron Tecnicaturas 2022 (modalidad B):
Se habilita un listado de actividades del sistema anterior de Créditos (CR).
El estudiante marca las actividades que haya completado.
Cada actividad CR se convierte automáticamente en Créditos ACA (CRE) según la tabla de equivalencias vigente.
2.4. Cálculo de la transición
Al confirmar la selección:
La aplicación calcula y muestra:
Plan 2018
Total de horas del plan: 3520 hs
Horas correspondientes a las materias aprobadas
Porcentaje de avance sobre el plan 2018
Plan 2025
Materias equivalentes aprobadas automáticamente
Créditos ACA obtenidos por:
Equivalencias completas
Equivalencias parciales (merge N→1)
Actividades CR → CRE
Total ACA acumulados sobre 30 requeridos
Porcentaje de avance total del Plan 2025 (horas + ACA)
2.5. Detalle de equivalencias
En el resultado se presenta un bloque desplegado por defecto que indica:
Código y nombre de la materia 2025
Materias 2018 que la completan
Modo de equivalencia:
Equivalencia directa
Merge N → 1
Parcial con ACA
Qué se completó y qué queda pendiente
3. Cálculo académico (criterios)
3.1. Equivalencias de materias
Las reglas se definen en el archivo mapping_rules.yaml, permitiendo:
1 → 1 (equivalencia directa)
N → 1 (requiere múltiples materias 2018)
Parcial con otorgamiento de ACA si no se completan todas
3.2. Créditos ACA
Los ACA se otorgan por:
Materias parcialmente equivalentes
Actividades CR reconocidas
Se acumulan hasta un máximo de 30 ACA, requeridos por el Plan 2025.
4. Módulo de Administración
El módulo Admin se encuentra disponible en la interfaz principal y está destinado a equipos de gestión académica.
4.1. Importación de catálogos (CSV)
Se pueden importar los siguientes archivos:
Materias Plan 2018 – Modalidad A
Materias Plan 2018 – Modalidad B
Materias Plan 2025
Actividades CR → CRE
Política de importación
Cada importación reemplaza completamente el catálogo correspondiente.
No se mezclan datos anteriores.
Evita duplicaciones y versiones inconsistentes.
⚠️ Importante:
Las selecciones realizadas por estudiantes no se borran al importar catálogos.
4.2. Limpieza de selecciones huérfanas
Disponible como acción manual.
El sistema elimina:
Selecciones de estudiantes que refieren a códigos de materias ya inexistentes.
Actividades CR que ya no existen en el catálogo actual.
Esta acción:
No modifica catálogos.
Requiere confirmación explícita.
Reporta cuántos registros fueron eliminados.
4.3. Auditoría – Transacciones de estudiantes
El sistema registra eventos de tipo:
SAVE_SELECTION – cada vez que un estudiante guarda su selección
Desde Admin se puede:
Visualizar el historial de transacciones
Ver fecha/hora, usuario, variante y resumen
Auditar uso y reconstruir escenarios académicos
La auditoría es:
Append-only (no se sobrescriben eventos)
Independiente de cambios en catálogos
Persistente entre sesiones
5. Consideraciones técnicas relevantes
Base de datos: SQLite
Persistencia desacoplada del frontend
Streamlit como interfaz única (sin backend separado)
Configuración portable (ideal para PythonAnywhere / Streamlit Cloud)
6. Buenas prácticas operativas
Importar catálogos solo cuando haya cambios oficiales.
Ejecutar limpieza únicamente si se modificaron códigos.
Verificar resultados con un usuario de prueba.
Usar la auditoría como respaldo institucional.
7. Alcance institucional
La aplicación:
No reemplaza al sistema académico oficial.
Funciona como herramienta de análisis, orientación y simulación.
Permite transparentar criterios de transición curricular.
Facilita la comunicación con estudiantes.