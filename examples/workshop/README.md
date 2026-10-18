# Ejemplo visible: de la oportunidad a AI-DLC

Puedes recorrer aquí los entregables del workshop antes de instalar herramientas. Son una **instantánea educativa generada**, con la hipótesis resuelta y las decisiones humanas pendientes. La ficha usa supuestos ilustrativos; estos archivos no demuestran ahorro comercial ni aprobación de un despliegue.

Fuente pública: commit [`68ed0fd2b78525345cdaeb9655e010e3a6a27f3d`](https://github.com/sjaramillov/agentic-transformation-workshop-latam/commit/68ed0fd2b78525345cdaeb9655e010e3a6a27f3d). El código, las guías y estos entregables originales se distribuyen bajo [MIT](../../LICENSE).

## Recorre el caso

| Paso | Entregable visible | Qué revisar |
| --- | --- | --- |
| 0. Formular valor | [Ejemplo resuelto](0-value.json) · [ficha para completar](0-value-worksheet.md) | Problema, hipótesis, línea base supuesta, objetivo, alternativas y parada |
| A. Entender el proceso | [EventStorming](A-eventstorming.json) | Actores, eventos, excepciones e invariantes |
| B. Elegir autonomía | [Oportunidades](B-opportunities.json) | Selección pedagógica y razones; las puntuaciones son supuestos |
| C. Diseñar el trabajo | [Workflow](C-workflow.json) | Aprobación, ejecución, recuperación y responsables |
| G. Conectar decisiones | [Matriz de trazabilidad](G-traceability.csv) | Métrica → caso → análisis → cambio → prueba → medición pendiente |
| AI-DLC: Inception | [Entrega de intención y requisitos](ai-dlc/inception.json) | Decisiones de producto, seguridad y operaciones |
| AI-DLC: Construction | [Entrega de construcción](ai-dlc/construction.json) | Unidades de trabajo y evidencia de aceptación |
| AI-DLC: Operations | [Entrega de operación](ai-dlc/operations.json) | Comprobaciones, medición y decisión de continuar |
| Decidir | [Registro de decisiones](ai-dlc/decisions.md) | Espacios pendientes para responsables, fecha y evidencia |

Para facilitar el ejercicio, usa la [guía de valor](../../FICHA_VALOR.md), la [integración de AI-DLC](../../AI_DLC.md), la [guía A–J](../../GUIA_REPLICACION.md) y el [agente ejecutable](../../AGENTE_EJECUTABLE.md). Las [plantillas actuales](../../workshop/templates/) permiten adaptar el caso. El [tablero del recorrido](../../diagramas/06-valor-ai-dlc.svg) muestra la conexión entre los entregables.

## Identidad y alcance de esta instantánea

El [manifiesto original](manifest.json) se conserva completo y sin modificaciones. El [recibo de copia](examples-verification.json) comprueba que los **10 entregables** publicados coinciden byte a byte con sus hashes en el manifiesto. Un hash demuestra identidad del archivo; las decisiones, pruebas y resultados requieren sus respectivas evidencias.

Esta carpeta contiene una selección de los artefactos preparados. El manifiesto también enumera código de aplicación, contextos y plantillas que ya están publicados en sus ubicaciones canónicas. Los campos `public_commit` y `source_sha256` identifican la versión pública y sus archivos; `analysis_commit` identifica los clones aislados creados por el preparador. No se duplican aquí esos clones ni sus directorios Git.

Las rutas `inputs` de los handoffs corresponden a una práctica completa generada. Para leer sus entradas en GitHub, abre los [contextos ARA/MODA](../../workshop/contexts/) y las [plantillas](../../workshop/templates/). Para ejecutar el recorrido completo, genera tu práctica con el comando siguiente.

Los tres handoffs mantienen `status: requires_human_review`; el manifiesto mantiene `human_decisions_approved: false` y `cloud_analysis_executed: false`. La [validación del agente](../../evidence/agent-workshop/README.md) y los [informes ARA/MODA históricos](../../evidence/mit/README.md) se vinculan a sus propios commits y fechas.

## Genera una copia editable

Desde la raíz de un clon del repositorio, con Git y Python 3.11+:

```bash
python3 scripts/workshop.py prepare \
  --revision 68ed0fd2b78525345cdaeb9655e010e3a6a27f3d \
  --output .local/mi-workshop
```

El comando prepara todos los artefactos y dos clones de análisis sin invocar AWS. El destino debe ser nuevo para conservar prácticas anteriores. Si quieres practicar con la versión vigente, sustituye el SHA por `HEAD`.

Edita la copia de tu práctica y registra allí las decisiones de tu equipo. Esta carpeta conserva el ejemplo de referencia. Las credenciales y estados privados del agente se crean durante cada ejecución y no forman parte de estos entregables.
