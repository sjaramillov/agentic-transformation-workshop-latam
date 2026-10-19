# Recursos públicos del workshop

Todos los materiales de la réplica están versionados:

| Recurso | Ubicación | Uso |
| --- | --- | --- |
| Reunión guiada | [facilitate.py](scripts/facilitate.py), [21 situaciones](workshop/discovery.json) | Preguntas, cliente, coach y sesión guardada |
| Tableros progresivos | [renderer](workshop/coach/boards.js) | Timeline, cuadrantes y carriles; exportación HTML autónoma |
| Aplicación, DB y E2E | [booking_lab](booking_lab/README.md) | Crear, consultar, cancelar, compensar y auditar |
| Ejemplo del discovery | [Conversación](examples/discovery/conversacion.md), [tableros completos](examples/discovery/tableros.html) | Referencia resuelta para facilitar la reunión |
| Caso y ejercicios A–C | [scenario.json](workshop/scenario.json) | Facilitar y modificar el ejemplo resuelto |
| Preparador | [workshop.py](scripts/workshop.py) | Generar práctica y repositorios de análisis |
| Contexto ARA | [ara.txt](workshop/contexts/ara.txt) | Alcance de agentes con escritura |
| Contexto MODA | [moda.txt](workshop/contexts/moda.txt) | Modernización sin infraestructura asumida |
| Transformación | [hardening](workshop/transformations/hardening/transformation_definition.md) | Corregir hallazgos y demostrar invariantes |
| Decisiones y comparación | [decisión](workshop/templates/decision.md), [CSV](workshop/templates/comparison.csv) | Trazabilidad de G–I |
| Tableros post-it | [galería](diagramas/README.md) | Explicación visual de A–J |
| Pruebas y resultados | [Resultados técnicos](evidence/README.md) | Referencia para comprobar tu ejecución |

## Fuentes oficiales

- [Agentic Readiness: método de evaluación](https://aws.amazon.com/blogs/migration-and-modernization/agentic-readiness/)
- [ARA y MODA como análisis administrados](https://aws.amazon.com/blogs/migration-and-modernization/new-in-aws-transform-analyze-your-code-for-modernization-and-agentic-readiness/)

- [AWS Transform: preparación](https://docs.aws.amazon.com/transform/latest/userguide/ct-getting-started.html)
- [Fuentes, análisis y remediación](https://docs.aws.amazon.com/transform/latest/userguide/ct-working-with.html)
- [Transformaciones personalizadas](https://docs.aws.amazon.com/transform/latest/userguide/custom-workflows.html)
- [Precios de Transform](https://aws.amazon.com/transform/pricing/)
- [PostgreSQL: locks](https://www.postgresql.org/docs/16/explicit-locking.html)
- [PostgreSQL: pg_dump](https://www.postgresql.org/docs/16/app-pgdump.html)
- [Psycopg: instalación](https://www.psycopg.org/psycopg3/docs/basic/install.html)
- [Rúbrica ARA: preguntas y puntuación](https://github.com/aws-samples/sample-agentic-readiness-analysis-orchestrator/tree/b48fd5ee1c94e56a7da76513ec388b6e00e886e5/definitions/managed/agentic-readiness-analysis/references)
- [Rúbrica MODA: preguntas, rutas y contrato](https://github.com/aws-samples/sample-agentic-readiness-analysis-orchestrator/tree/b48fd5ee1c94e56a7da76513ec388b6e00e886e5/definitions/managed/modernization-readiness-analysis/references)
- [AWS Samples: Portfolio Analysis Orchestrator](https://github.com/aws-samples/sample-agentic-readiness-analysis-orchestrator)

## Páginas del evento

Estas páginas pertenecen al evento `Agentic Transformation Workshop for LATAM partners` en Workshop Studio y pueden dejar de estar disponibles al expirar el evento.

| Tema | Enlace |
| --- | --- |
| Portada, objetivos, prerrequisitos y duración | [Agentic Transformation Workshop](https://catalog.us-east-1.prod.workshops.aws/event/dashboard/en-US/workshop) |
| Preparación | [Getting started](https://catalog.us-east-1.prod.workshops.aws/event/dashboard/en-US/workshop/00-getting-started) |
| Cuenta temporal del evento | [At an AWS event](https://catalog.us-east-1.prod.workshops.aws/event/dashboard/en-US/workshop/00-getting-started/aws-event) |
| IDE y paquetes | [Open the IDE](https://catalog.us-east-1.prod.workshops.aws/event/dashboard/en-US/workshop/00-getting-started/ide-setup) |
| Kiro CLI | [Configure Kiro CLI](https://catalog.us-east-1.prod.workshops.aws/event/dashboard/en-US/workshop/00-getting-started/kiro-cli-setup) |
| Fuente y acceso de ATX | [Confirm ATX access and source repos](https://catalog.us-east-1.prod.workshops.aws/event/dashboard/en-US/workshop/00-getting-started/atx-server-setup) |
| A. EventStorming | [Model the process with the room](https://catalog.us-east-1.prod.workshops.aws/event/dashboard/en-US/workshop/01-eventstorming) |
| B. Complejidad cognitiva | [Where does the process need an agent?](https://catalog.us-east-1.prod.workshops.aws/event/dashboard/en-US/workshop/02-cognitive-complexity) |
| C. Workflow del agente | [Design the agent workflow](https://catalog.us-east-1.prod.workshops.aws/event/dashboard/en-US/workshop/03-agentic-workflow-design) |
| D. ARA | [Run Agentic Readiness Analysis](https://catalog.us-east-1.prod.workshops.aws/event/dashboard/en-US/workshop/04-run-ara) |
| E. MODA | [Run Modernization Analysis](https://catalog.us-east-1.prod.workshops.aws/event/dashboard/en-US/workshop/05-run-mod) |
| F. Portafolio (opcional) | [Scale to the full estate](https://catalog.us-east-1.prod.workshops.aws/event/dashboard/en-US/workshop/06-run-portfolio) |
| G. Hoja de ruta | [Build the modernization roadmap with Kiro](https://catalog.us-east-1.prod.workshops.aws/event/dashboard/en-US/workshop/07-review-prioritize) |
| H. Remediar | [Continuous Remediation: Modernize & Unblock](https://catalog.us-east-1.prod.workshops.aws/event/dashboard/en-US/workshop/08-execute-transformation) |
| I. Volver a medir | [Re-measure](https://catalog.us-east-1.prod.workshops.aws/event/dashboard/en-US/workshop/09-remeasure) |
| J. Modelo operativo | [Operating CI/CD/CM in Your Organization](https://catalog.us-east-1.prod.workshops.aws/event/dashboard/en-US/workshop/10-operating-model) |
| Próximo capítulo | [AI DLC for agent building](https://catalog.us-east-1.prod.workshops.aws/event/dashboard/en-US/workshop/11-ai-dlc-next) |
| Limpieza | [Cleanup](https://catalog.us-east-1.prod.workshops.aws/event/dashboard/en-US/workshop/99-cleanup) |

## Referencias externas mencionadas

- [Documentación de AWS Transform](https://docs.aws.amazon.com/transform/)
- [Kiro](https://kiro.dev/)
- [Catálogo de workshops de AWS Builder Center](https://builder.aws.com/build/workshops)
- [Precios de Amazon EC2](https://aws.amazon.com/ec2/pricing/)
- [Precios de Amazon Bedrock](https://aws.amazon.com/bedrock/pricing/)
- [Precios de Amazon CloudFront](https://aws.amazon.com/cloudfront/pricing/)


Las páginas del evento son referencias de procedencia. El recorrido público A–J está explicado en [GUIA_REPLICACION.md](GUIA_REPLICACION.md) y funciona con los archivos de este repositorio.
