# ARA y MODA sobre Booking MIT en CCS

Esta evaluación utiliza exclusivamente el código original público de `booking_lab/`. Fecha: 16 de octubre de 2026. ATX 3.19.0, región us-east-1, fuentes locales aisladas y definiciones administradas de AWS Transform.

## Base medida

- Commit público inicial: `e338a6b99cba389cbb5d96ca21a12d660071b28d`.
- Commit de los repositorios de análisis iniciales: `0de82bb93ace5949e4e817e28fc8417017f526c9`.
- ARA inicial: `01M52NHWT3HN22WGGVTK4491AJ`, completo; 29 hallazgos y cobertura de 43 preguntas (14 evaluaciones adicionales).
- Clasificación inicial: **Remediation Required**, 1 BLOCKER, 9 RISK-SAFETY, 11 RISK-QUALITY y 8 INFO.
- Bloqueador: **AUTH-Q6**, integridad de auditoría frente al administrador de la base de reservas. STATE-Q1 ya pasó con la saga durable original.

## Correcciones

1. Ledger de auditoría independiente con volumen y clave propios, hash encadenado y firma HMAC. PostgreSQL conserva una proyección. Pruebas de modificación, truncamiento, privilegios, reinicio y restauración.
2. Scope `bookings:cancel` independiente de `bookings:write`.
3. Validación de NumericDate: rechazo de NaN, infinitos, booleanos y duración excesiva.
4. Demo interactiva y cliente público para crear, listar y cancelar.
5. Guías A–J, escenario, contextos, transformación y plantillas completamente públicos; la documentación antigua se conserva en `historico/`.

## Incidente de MODA

La ejecución inicial `01M52NJ3F87P2G8G66AGM7234T` devolvió `complete` y cero hallazgos, pero no produjo informes. La metadata del agente registra un error interno del servicio a las 15:50:45 UTC. Se conserva como intento fallido, sin interpretar ese cero como aprobación. Repetición sobre la misma fuente/contexto: `01M52PQ865PSNWRJPWACQA9X12`.

## Comparación posterior

La versión corregida se congeló en los clones de análisis con SHA `b1f49daa78174a34535508ee4e2fa5effa39e11c`. La comparación final se completará con los informes verificados de esa versión y sus hashes.

Consulta [la implementación](LABORATORIO_MIT.md), [los comandos reproducibles](EJECUCION_AWS.md) y [la prueba de DB](CCS_DATABASE_E2E.md). Los antecedentes del otro ejemplo se conservan en [Histórico](historico/CCS_E2E.md).
