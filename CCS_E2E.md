# ARA y MODA sobre Booking MIT en CCS

**Registro histórico del 16 de octubre de 2026.** Los resultados de esta página pertenecen a los commits indicados en la tabla. El agente ejecutable y la aprobación que ahora valida la API se incorporaron después; su [aceptación técnica](AUDITORIA_E2E.md) no cambia retroactivamente estas puntuaciones ni cierra hallazgos del evaluador.

**ARA pasó de 1 a 0 bloqueadores.** La versión corregida recibió **Pilot-Ready (Safety Concerns)** y pasó los **18 escenarios E2E con PostgreSQL** en CCS y GitHub Actions. Todo el código de entrada, los contextos, la transformación original, las pruebas y los informes aceptados están publicados. [Índice de evidencia](evidence/mit/README.md).

Las fuentes `local` de Transform son clones del código público dentro de CloudShell. El campo `compute_mode: LOCAL` describe la ejecución del cliente de análisis en CCS; el código y los resultados aceptados están disponibles en GitHub.

Fecha: 16 de octubre de 2026. ATX 3.19.0, us-east-1, definiciones administradas de AWS Transform y agentes con alcance `write-enabled`.

## Comparación controlada

| Medición | Antes | Después |
| --- | --- | --- |
| Fuente pública | `e338a6b99cba389cbb5d96ca21a12d660071b28d` | `401e5317567f3500843bc722893bf6d22b733390` |
| Fuente en clones de análisis | `0de82bb93ace5949e4e817e28fc8417017f526c9` | `b1f49daa78174a34535508ee4e2fa5effa39e11c` |
| ARA | Remediation Required | Pilot-Ready (Safety Concerns) |
| BLOCKER | 1 | **0** |
| RISK-SAFETY | 9 | **8** |
| RISK-QUALITY / INFO | 11 / 8 | 11 / 8 |
| Hallazgos ARA | 29 | 27 |
| Preguntas representadas ARA | 43 | 43 |
| MODA: clasificación | Remediation Required | Remediation Required |
| MODA: puntuación informada | 2.02 / 4 | 1.99 / 4 |
| MODA: High / Medium / Low | 4 / 19 / 8 | 5 / 19 / 11 |
| Hallazgos MODA | 31 | 35 |

ARA inicial: `01M52NHWT3HN22WGGVTK4491AJ`. ARA posterior: `01M52Q045MKCVHRGRYRSEN2A6T`, terminado a las 16:15:29 UTC. Los cuatro artefactos de cada informe pasaron verificación independiente de estructura, conteos, unicidad y cobertura. [Comparación JSON](evidence/mit/comparison/ara/comparison.json) y [CSV por pregunta](evidence/mit/comparison/ara/comparison.csv).

Los contextos y el alcance de archivos fueron iguales antes/después; [hashes de contextos](evidence/mit/context-sha256.json). Se analizaron `booking_lab/`, `LICENSE` y un `.gitignore` generado. La CI, pruebas unitarias y guías de la raíz se verificaron por separado. Los hashes del código posterior coinciden exactamente entre el commit público, ambos clones de análisis, el E2E de CCS, la demo y el E2E de GitHub Actions: [procedencia](evidence/mit/provenance.json).

## Qué se corrigió y cómo se demostró

| Pregunta / problema | Cambio | Resultado comprobado |
| --- | --- | --- |
| **AUTH-Q6: BLOCKER** | Ledger independiente del administrador de la DB, clave y volumen propios, hash encadenado, HMAC, retención mínima de 90 días y checkpoint externo | ARA: **pass**. E2E: manipulación y truncamiento detectados, reinicio y backup restaurado, DB admin sin acceso al ledger |
| **AUTH-Q3: RISK-SAFETY** | Scope `bookings:cancel` separado de `bookings:write` | ARA: **pass**. Tokens de creación no cancelan; tokens de cancelación no crean |
| Fechas JWT inválidas | Rechazo de NaN, infinitos, booleanos, fechas inconsistentes y duración excesiva | Pruebas unitarias y negativas HTTP aprobadas |
| Imagen incompleta | Incluir `audit.py` explícitamente en `.dockerignore` | Build y 18 casos aprobados en CCS y CI |
| Disco lleno en CCS | Limpieza acotada de contenedores detenidos de la práctica, conservando logs y volúmenes | 6.6 GiB recuperados; nueva corrida completa aprobada |
| Materiales difíciles de replicar | Código original MIT, demo, cliente, preparador, escenarios, contextos, TD y comparador públicos | Clon público, preparación reproducible, pruebas públicas sin archivos del evento |

**STATE-Q1**, compensación y rollback, ya pasó en la primera evaluación MIT y siguió pasando después. La saga durable corrige el problema observado en el ejemplo anterior; no se contabiliza como un segundo bloqueador nuevo de esta comparación.

ARA cambió `API-Q6` y `STATE-Q7` de `not_evaluated_extended` a `pass`. Los controles correspondientes ya existían: se registra como variación de aplicación de la rúbrica, sin atribuir dos correcciones adicionales al código. AWS no devolvió una versión inmutable de las definiciones administradas; se conserva su nombre y la versión del CLI. Una repetición futura puede producir juicios distintos.

## MODA

El intento inicial válido fue `01M52RMNGR77M5PG3VPWBNJ9QJ`, terminado a las **16:51:12 UTC**: **4 High, 19 Medium, 8 Low**, puntuación **2.02/4**. [Informe inicial completo](evidence/mit/before/moda/booking-mit-mod-report.md). La repetición inicial se ejecutó después del análisis de la versión corregida debido a dos errores del servicio; “antes” y “después” identifican las versiones de código, no el orden de finalización.

Ambos conjuntos incluyen **37 preguntas representadas** y pasaron verificación de los cuatro artefactos. [Comparación MODA JSON](evidence/mit/comparison/moda/comparison.json) y [CSV](evidence/mit/comparison/moda/comparison.csv).

La evaluación posterior `01M52Q232A5BYEPH5V20Y8FYWP` terminó a las 16:14:06 UTC. Resultado: **Remediation Required**, puntuación **1.99**, **5 High, 19 Medium, 11 Low**. [Informe completo](evidence/mit/after/moda/booking-mit-mod-report.md), [JSON](evidence/mit/after/moda/booking-mit-mod-report.json) y [verificación](evidence/mit/after/moda-verification.json).

### Cómo interpretar la variación

La puntuación informada pasó de **2.02 a 1.99** y los High de **4 a 5**. No se usa ese delta como medida causal de regresión: cambió el conjunto de preguntas activas por la interpretación de las banderas del runtime, y el ledger añadió requisitos operativos.

| Pregunta | Antes → después | Revisión |
| --- | --- | --- |
| AUTH-Q6 (ARA) | BLOCKER → pass | Cierre respaldado por implementación y E2E |
| APP-Q2 (MODA) | Medium → Low | El auditor reconoció el ledger como proceso/almacén separado; se conserva la frontera de pagos por HTTP |
| DATA-Q1 | pass (4) → High (1) | El ledger y sus checkpoints añaden artefactos con retención; falta archivo automático fuera del host |
| INF-Q9 / OPS-Q5 / OPS-Q7 | No evaluadas → Medium / High / Low | Antes `has_deployed_workload=false`; después `true`. También cambió `has_multi_instance_deployment`. Se muestra esa variación de alcance sin inventar un despliegue productivo |
| INF-Q10 | High → Medium | El evaluador dio más crédito al runner imperativo. Sigue faltando IaC para el entorno operado; no se cierra la brecha |
| DATA-Q4 | Medium → Low | Cambió el juicio sobre complejidad SQL; `schema.sql` es idéntico en ambas versiones. No se atribuye a una corrección de esquema |

Para ARA se utiliza `native_severity`: `BLOCKER` y `RISK-SAFETY` son categorías diferentes, aunque ambas pueden normalizarse como High. La clasificación MODA sigue su propia regla. La revisión no mezcla esos conteos.

### Revisión de los cinco High

| Pregunta | Lectura del informe | Revisión con evidencia |
| --- | --- | --- |
| INF-Q2 | Bases administradas y failover | PostgreSQL y SQLite funcionan en el laboratorio; no se desplegó RDS/Multi-AZ. Es una brecha de operación externa |
| INF-Q11 | Ausencia de CI/CD | El clon reducido no contenía `.github/workflows`. El repo completo sí tiene [pipeline](.github/workflows/checks.yml) y [ejecución aprobada](https://github.com/sjaramillov/agentic-transformation-workshop-latam/actions/runs/38929875432). Publicación de imagen, escaneo y despliegue continuo siguen fuera de esa CI |
| DATA-Q1 | Archivo durable fuera del host | Los snapshots/checkpoints se generan y verifican; no existe archivo automático en S3 Object Lock. Requiere una decisión de despliegue y retención |
| SEC-Q2 | Cifrado en reposo | El código no configura cifrado propio/KMS. AWS documenta [cifrado del almacenamiento de CloudShell](https://docs.aws.amazon.com/cloudshell/latest/userguide/data-encryption.html); la ausencia de IaC no demuestra ausencia de cifrado del host. No se verificó la configuración efectiva del volumen del daemon ni claves administradas por el cliente |
| OPS-Q5 | Despliegue gradual y rollback | Las pruebas reinician contenedores y restauran datos. No constituyen un rollout productivo ni prueban compatibilidad entre versiones de esquema |

Se conservan los juicios originales del evaluador. El resultado MODA no invalida el funcionamiento del workshop; identifica trabajo para convertir su runtime en un servicio operado. Las propuestas de RDS, ECS o S3 no representan recursos desplegados ni una obligación de usar EKS.

## Riesgos de ARA que permanecen

Los ocho RISK-SAFETY son `AUTH-Q4` (delegación), `AUTH-Q5` (gestión/rotación de credenciales), `AUTH-Q7` (suspensión individual), `STATE-Q4` (circuit breaker/backoff), `STATE-Q5` (límites de tasa/concurrencia), `STATE-Q6` (presupuesto acumulado), `HITL-Q1` (borrador revisable) y `HITL-Q2` (puerta de aprobación configurable).

Para repetir el workshop se utilizan pagos sintéticos, identidades de prueba y puertos en loopback. En esta versión histórica la confirmación del módulo C no era una puerta implementada en la API. El runner no aplicó límites cgroup y registró `resource_limits_available: false`; una revisión posterior detectó un nombre de campo CPU incorrecto, por lo que ese indicador no determina por sí solo la capacidad real de CloudShell. El ledger detecta alteraciones frente al administrador de la DB; su [frontera de confianza](booking_lab/AUDIT.md) no protege frente a un administrador del host con todas las claves y checkpoints. Estas condiciones explican el calificativo **Safety Concerns**; no hay aprobación de producción.

## Evidencia funcional y transformación

- [DB en CCS](evidence/mit/runtime/final-db-e2e-02.json): **18/18**, 35 eventos de auditoría, cinco invariantes en cero, restauración PostgreSQL y SQLite, cero contenedores activos al terminar.
- [Demo manual](evidence/mit/runtime/manual-demo-verification.json): crear, consultar, aislar sujetos, cancelar y repetir con las mismas respuestas.
- [DB en GitHub Actions](evidence/mit/runtime/github-actions-db-e2e.json): **18/18**, sobre el mismo código.
- La [transformación original](workshop/transformations/hardening/transformation_definition.md) se publicó en CCS con versión `3h27i6pk9alc7pwhfldlj9bz`; [recibo HTTP 200](evidence/mit/runtime/td-publish-03.json). Las correcciones de esta comparación se implementaron directamente y se evaluaron con ARA/MODA; no se atribuyen a una ejecución de esa TD.

## Incidentes conservados

MODA inicial tuvo dos respuestas `complete` con `findingCount: 0` y ningún informe: `01M52NJ3F87P2G8G66AGM7234T` y `01M52PQ865PSNWRJPWACQA9X12`. Sus sesiones registraron `An internal server error occurred` a las 15:50:45 y 16:25:43 UTC. Ambos son **intentos inválidos**, nunca resultados sin hallazgos. El tercer intento, sin otros análisis simultáneos y con idéntico código/contexto, produjo el conjunto válido. [Registro verificable de incidentes](evidence/mit/incidents.json). La guía exige los cuatro artefactos y su verificación para aceptar una ejecución.

El fallo por espacio de Docker se conserva en [su JSON original](evidence/mit/runtime/final-db-e2e.json); la prueba aceptada tiene otro archivo e inicio. La [guía de CloudShell](CLOUDSHELL.md) incorpora el procedimiento de limpieza.

## Reproducir y continuar

[Inicio rápido](INICIO_RAPIDO.md) → [guía A–J](GUIA_REPLICACION.md) → [comandos ARA/MODA y antes/después](EJECUCION_AWS.md) → [comparador](scripts/compare_reports.py). Los antecedentes del otro ejemplo están en [Histórico](historico/CCS_E2E.md).
