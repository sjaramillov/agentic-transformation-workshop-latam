# Recursos del taller

## Paquete local del IDE (no publicado)

La captura local `resources/agentic-workshop-materials-2026-10-15.tar.gz` incluye `apps/travelcorp-portfolio`, el directorio `orchestrator` del IDE de esa sesión y los informes existentes al capturar. Contiene código de ejemplo, resultados precomputados y estado de ejercicios A–C; no incluye credenciales de AWS. El archivo sigue en la carpeta local original, pero está excluido del repositorio público: no se encontró una licencia de redistribución para TravelCorp y no se le aplica la MIT de esta guía.

El informe ARA activo clasifica `booking-service` como `Not Agent-Integrable` con 5 bloqueadores; la página muestra un ejemplo estático con 6. No había MODA consolidado en `reports/`, pero la auditoría encontró su conjunto de cuatro artefactos dentro de `src/booking-service/services/booking-service/modernization-readiness-analysis/`. La consulta posterior al IDE mostró la ejecución anterior como `complete`. Ese JSON declara `Not Ready` por puntuación y `Remediation Required` por conteo, con una marca explícita de divergencia: conserva ambas lecturas, no normalices el dato. El paquete también contiene un baseline precomputado; ninguno de estos informes es resultado de una nueva réplica. Su checksum local está en [`CHECKSUMS.txt`](CHECKSUMS.txt).

## Repositorio público de AWS

[AWS Samples: Portfolio Analysis Orchestrator](https://github.com/aws-samples/sample-agentic-readiness-analysis-orchestrator) es un proyecto complementario. La copia local consultada estaba en el commit `b48fd5ee1c94e56a7da76513ec388b6e00e886e5` (14 de octubre de 2026); este repositorio enlaza al upstream en vez de duplicarlo.

La versión pública capturada contiene una carpeta `advisor/`; el IDE del evento contenía una carpeta `orchestrator/` distinta. El paquete local conserva la versión que acompañaba al taller.

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

## Diagramas originales del módulo J y tableros de esta guía

La página vincula cinco PNG bajo `workshop/static/images/operating-model/`; sus rutas y descripciones están en [`assets/README.md`](assets/README.md). La ruta directa entregó una página del sitio y la navegación del evento devolvió “Page not found” al momento de la captura; no se guardaron respuestas HTML como imágenes. Esta guía incluye tableros explicativos originales en [`diagramas/`](diagramas/README.md); no son copias de esos PNG.

## Referencias contrastadas durante la auditoría

- [Prerequisitos de continuous modernization](https://docs.aws.amazon.com/transform/latest/userguide/ct-getting-started.html)
- [Fuentes, análisis, IDs y remediación](https://docs.aws.amazon.com/transform/latest/userguide/ct-working-with.html)
- [Publicación y versiones de TD](https://docs.aws.amazon.com/transform/latest/userguide/custom-workflows.html)
- [Categorías de TD](https://docs.aws.amazon.com/transform/latest/userguide/custom.html)
- [Diagnóstico de ATX](https://docs.aws.amazon.com/transform/latest/userguide/ct-troubleshooting.html)

La documentación pública y el CLI del evento pueden diferir. Conserva `atx --version` y consulta `--help` antes de incorporar un flag nuevo.
