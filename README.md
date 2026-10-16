# Agentic Transformation Workshop AWS Guide

Laboratorio práctico en español con **código original MIT**, PostgreSQL, API de reservas, pagos simulados, auditoría durable y pruebas de recuperación. Incluye la guía de AWS Transform, EventStorming, ARA/MODA y cinco tableros visuales tipo post-it.

## Ejecuta la réplica completa

```bash
git clone https://github.com/sjaramillov/agentic-transformation-workshop-latam.git
cd agentic-transformation-workshop-latam
python3 booking_lab/run.py e2e --output .local/db-e2e.json
```

Necesitas Python 3.11+ y Docker. El comando crea la DB y dos instancias de API, prueba el flujo y sus fallos, guarda evidencia y detiene sus contenedores. **Todo el código necesario está en este repo público.** Lee [el laboratorio MIT](LABORATORIO_MIT.md) para conocer su contrato, garantías y ejecución en CCS.

## Empieza aquí

- **[Laboratorio completo MIT](LABORATORIO_MIT.md)**: flujo con PostgreSQL y pruebas desde un clon público.
- [Inicio rápido](INICIO_RAPIDO.md): clona y ejecuta el workshop público completo.
- [Auditoría E2E](AUDITORIA_E2E.md): capas de verificación y evidencia.
- [Ejecución AWS](EJECUCION_AWS.md): acceso, rutas, publicación de TD y aceptación.
- [Pruebas del contenedor](RUNTIME_LOCAL.md): detectar y corregir fallos de empaquetado y sondas.
- [Preparación con CloudShell](CLOUDSHELL.md): recorrido comprobado para una cuenta propia.
- [Revisión de las TD](LIMITACIONES_TD.md): criterios para aceptar una remediación.
- [Guía de réplica](GUIA_REPLICACION.md): requisitos, secuencia de módulos, comandos y puntos de verificación.
- [Tableros visuales](diagramas/README.md): cinco diagramas originales tipo post-it sobre el flujo y sus controles.
- [Prompts reutilizables](PROMPTS.md): mapeo, priorización y comparación con evidencia.
- [Fuentes y recursos](RECURSOS.md): páginas del evento y referencias de AWS/Kiro.
- [Alcance de licencias y atribución](NOTICE.md).

## Estado de reproducción

La réplica MIT pasó **17 escenarios E2E en CCS con PostgreSQL real**, incluyendo reservas, consultas, cancelación, pagos, compensación y auditoría. Consulta [la evidencia de DB](CCS_DATABASE_E2E.md). Sus pruebas incluyen concurrencia entre dos instancias, caídas de proceso/DB/proveedor, reentrega de eventos y restauración de datos. El [laboratorio completo](LABORATORIO_MIT.md) explica cómo ejecutarlas y conservar sus resultados.

La [evaluación ARA/MODA en CCS](CCS_E2E.md) registra los análisis del código MIT, la comparación y las correcciones.

## Tableros

![EventStorming: viaje de reserva y recuperación](diagramas/01-eventstorming.svg)

![Oportunidades y autonomía](diagramas/02-oportunidad-agente.svg)

![Workflow con aprobación humana](diagramas/03-workflow-rebooking.svg)

![Ciclo de análisis, remediación y nueva medición](diagramas/04-ciclo-ara-moda.svg)

![Responsabilidades y puertas operativas](diagramas/05-modelo-operativo.svg)

## Recorrido resumido

1. Modelar la experiencia y sus excepciones (A).
2. Decidir dónde un agente aporta valor y qué autonomía puede tener (B–C).
3. Evaluar seguridad para agentes con ARA y rutas de modernización con MODA (D–E); ampliar al portafolio si hace falta (F).
4. Priorizar con evidencia y aplicar cambios revisables en una rama local (G–H).
5. Repetir análisis con el mismo alcance y operar el ciclo con dueños y controles claros (I–J).

Los diagramas son esquemas explicativos, no reproducciones literales de los tableros del evento ni reportes de métricas. Sus decisiones siguen los ejemplos descritos en la guía.

## Materiales incluidos

Código de aplicación, esquema PostgreSQL, pruebas, escenario de negocio, ejercicios A–C, contextos ARA/MODA, transformación original y plantillas de comparación. Genera una práctica con:

```bash
python3 scripts/workshop.py prepare --output .local/workshop-01
```

La [guía A–J](GUIA_REPLICACION.md) enlaza cada paso con su recurso público. Para D–I necesitas tu cuenta y acceso a AWS Transform. Los documentos de la primera implementación están en [el archivo histórico](historico/README.md).

## Fuentes

El taller original está en [AWS Workshop Studio](https://catalog.us-east-1.prod.workshops.aws/event/dashboard/en-US/workshop). La lista completa de módulos y referencias está en [RECURSOS.md](RECURSOS.md). El repositorio público complementario de AWS es [sample-agentic-readiness-analysis-orchestrator](https://github.com/aws-samples/sample-agentic-readiness-analysis-orchestrator); no está copiado dentro de este repositorio.

## Licencia

El código original de la réplica, sus pruebas, scripts, guía y diagramas se distribuyen bajo [MIT](LICENSE). Las referencias a proyectos externos se identifican en [NOTICE.md](NOTICE.md).
