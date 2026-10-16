# Workshop completo A–J con código original MIT

Caso: un agente ayuda a crear, consultar y cancelar reservas. El servicio ejecuta pagos sintéticos, conserva el estado en PostgreSQL y recupera operaciones interrumpidas. La aplicación, escenario, contextos, plantillas, transformación y pruebas están incluidos en el repo. La cuenta del evento y sus paquetes no forman parte de los requisitos.

Comienza con [Inicio rápido](INICIO_RAPIDO.md). El comando `scripts/workshop.py prepare` genera una práctica nueva desde un commit público, sin sobrescribir otra práctica.

| Módulo | Actividad | Recurso público | Entregable / aceptación |
| --- | --- | --- | --- |
| A | Modelar eventos y excepciones | [Escenario](workshop/scenario.json), [tablero 1](diagramas/01-eventstorming.svg) | `A-eventstorming.json`: eventos, actores e invariantes |
| B | Elegir una oportunidad y autonomía | Escenario, [tablero 2](diagramas/02-oportunidad-agente.svg) | `B-opportunities.json`: decisión y riesgos |
| C | Diseñar el workflow | Escenario, [tablero 3](diagramas/03-workflow-rebooking.svg) | `C-workflow.json`: confirmaciones, pasos y dueños |
| D | Evaluar seguridad para agentes | [Contexto ARA](workshop/contexts/ara.txt) | Informe real, ID, commit y hallazgos |
| E | Evaluar modernización | [Contexto MODA](workshop/contexts/moda.txt) | Informe real con propuestas separadas del runtime |
| F | Leer el portafolio | Las dos fuentes aisladas de análisis | Inventario; un servicio con tres roles de proceso |
| G | Priorizar | [Plantilla](workshop/templates/decision.md), [prompts](PROMPTS.md) | Hallazgo → cambio → prueba → responsable |
| H | Corregir | [Transformación original](workshop/transformations/hardening/transformation_definition.md) | Diff revisado y pruebas de regresión |
| I | Volver a medir | Mismos contextos y alcance de D/E | [Comparación CSV](workshop/templates/comparison.csv), informes antes/después |
| J | Operar y repetir | [Tablero 5](diagramas/05-modelo-operativo.svg), CI público | Evidencia de DB, restore, propietario y cierre |

## A. Facilita EventStorming

Lee `workshop/scenario.json` y dibuja el recorrido solicitado → cobrado → confirmado. Añade cancelación → reembolso y el caso cobrado → fallo de DB → compensación. Discute qué ocurre si se pierde la respuesta HTTP después de un commit. Asocia cada transición con `operations`, `bookings`, `charges`, `outbox` y `audit_events` del [esquema](booking_lab/schema.sql).

Ejercicio: añade una excepción al escenario y explica qué estado durable permite retomarla. El entregable inicial es un ejemplo resuelto; el participante debe justificar sus cambios.

## B. Decide el alcance del agente

El ejemplo compara un asistente de reservas con uno de auditoría. Los valores numéricos son supuestos pedagógicos editables. El asistente de reservas prepara una propuesta y espera confirmación antes de escribir. El servidor valida identidad y scopes y aísla las reservas por sujeto. La política conversacional de confirmación se diseña aquí; una aplicación de agente que use este backend debe implementarla.

## C. Diseña el workflow

Define intención, confirmación, llamada, consulta de estado y recuperación. Una respuesta ambigua se reintenta con la misma identidad, payload y `Idempotency-Key`. Cambiar la clave puede crear otra operación. El [tablero de rebooking](diagramas/03-workflow-rebooking.svg) ilustra el patrón proponer → aprobar → ejecutar; el backend incluido implementa creación y cancelación, que son las operaciones de esta práctica.

## D–F. Ejecuta análisis reales

Sigue [Ejecución AWS](EJECUCION_AWS.md). ARA y MODA reciben clones separados del mismo código para evitar interferencias. En F el portafolio mínimo es este servicio; API, pagos y worker son roles dentro del mismo repo. Para ampliarlo, incorpora tus propios servicios con licencia compatible y repite descubrimiento. No hace falta inventar tres repositorios de ejemplo.

## G. Prioriza con evidencia

Para cada hallazgo comprueba el archivo y comportamiento citado. Clasifica como confirmado, corregido, falso positivo con prueba o pendiente con causa. Atiende primero autorización, integridad de pagos y recuperación. Usa la [plantilla de decisión](workshop/templates/decision.md). Una puntuación no sustituye una prueba del contrato.

## H. Remedia

Trabaja en una rama de un clon nuevo. Puedes implementar la corrección directamente o usar la TD pública incluida. Conserva la revisión antes de integrar. Ejecuta las pruebas del contrato y el E2E con DB. Revisa que los roles no hayan recibido privilegios administrativos, que los reintentos conserven claves y que no se haya reemplazado persistencia por memoria.

## I. Compara

Ejecuta de nuevo ARA y MODA con el mismo contexto y alcance `write-enabled`. Compara por `question_id`, conserva ID, fecha, versión de ATX, hashes y SHA. La [evidencia en CCS](CCS_E2E.md) muestra las mediciones de esta réplica. Distingue variaciones del evaluador de cambios demostrados en código.

## J. Cierra el ciclo

Producto acepta intención y autonomía; ingeniería revisa código; seguridad revisa identidad y auditoría; operaciones comprueba recuperación y restauración. La CI ejecuta las pruebas públicas y el E2E de DB. Al terminar el runner detiene sus contenedores y conserva el volumen y logs para revisión. No borres datos o recursos ajenos al prefijo de la práctica.

## Materiales y licencia

La réplica original completa se publica bajo [MIT](LICENSE). [Recursos](RECURSOS.md) reúne todos los archivos necesarios y fuentes oficiales. La documentación anterior está en [Histórico](historico/README.md), fuera del recorrido vigente.
