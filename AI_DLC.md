# Integrar el workshop en AI-DLC

**Objetivo:** convertir una oportunidad de negocio en requisitos, cambios revisables y evidencia que permita decidir el siguiente paso. El agente de desarrollo propone planes y artefactos; las personas responsables aceptan la intención, el alcance y las decisiones críticas.

AWS organiza AI-DLC en **Inception**, **Construction** y **Operations**, con contexto acumulado y validación humana. La tabla siguiente es la adaptación de este repositorio a esas fases, basada en la [descripción oficial de AI-DLC](https://aws.amazon.com/blogs/devops/ai-driven-development-life-cycle/).

## Un recorrido, tres entregas

| Fase | Entrada | Actividad del workshop | Artefactos de salida | Responsable y condición para avanzar |
| --- | --- | --- | --- | --- |
| **Inception** | Problema, evidencia del proceso y alternativas | Ficha de valor; EventStorming A; oportunidad B; autonomía C; lectura inicial ARA/MODA D–F | Hipótesis, métricas, límites, requisitos y unidades de trabajo | Producto acepta problema/objetivo y alternativa; seguridad acepta el límite de autonomía. Sin línea base, registrar una tarea de medición |
| **Construction** | Requisitos aceptados, contexto y hallazgos comprobados | Priorización G; cambios H; agente con aprobación; pruebas de DB y evaluación I | Código revisado, pruebas, trazabilidad y decisiones técnicas | Ingeniería revisa; seguridad verifica identidad/aprobación; cada requisito tiene una prueba de aceptación |
| **Operations** | Aplicación y resultados de sus pruebas | Recuperación, restauración, observación y cierre J; medición de valor | Recibo de ejecución, runbook, dueño y decisión de continuar | Operaciones acepta recuperación; producto revisa resultados. Un despliegue productivo exige su propia infraestructura y validación |

Repite ARA/MODA cuando cambien código, contexto o alcance. Usa sus hallazgos para priorizar requisitos y verifica el comportamiento con pruebas. Evalúa la calidad del modelo y el valor de negocio con las métricas de la ficha de valor.

## Preparar los artefactos de una práctica

Desde un clon público:

```bash
python3 scripts/workshop.py prepare --output .local/workshop-01
```

El preparador toma la aplicación, escenario, contextos y plantillas registrados en Git, y guarda su procedencia en `manifest.json`. Registra tus cambios en Git antes de preparar una práctica; los cambios pendientes quedan fuera. Elige un directorio de salida nuevo para cada práctica.

Las siguientes rutas son relativas al directorio elegido con `--output`, por ejemplo `.local/workshop-01/`.

| Archivo generado | Para qué sirve |
| --- | --- |
| `0-value.json` | Ejemplo de oportunidad, métricas, alternativas y condiciones de parada |
| `0-value-worksheet.md` | Ficha vacía para la decisión de tu equipo |
| `A-eventstorming.json` | Eventos, actores, excepciones e invariantes |
| `B-opportunities.json` | Alternativas y selección pedagógica |
| `C-workflow.json` | Pasos, autonomía y responsables |
| `G-traceability.csv` | Requisito → métrica → hallazgo → cambio → prueba → medición |
| `ai-dlc/inception.json` | Contexto y decisiones pendientes de producto/seguridad |
| `ai-dlc/construction.json` | Unidades de trabajo, aceptación y evidencias requeridas |
| `ai-dlc/operations.json` | Runbook, métricas, responsables y criterio de continuación |
| `ai-dlc/decisions.md` | Registro vacío de decisiones humanas con fecha y evidencia |
| `contexts/` y `sources/` | Contextos y clones aislados para ARA/MODA |

Los archivos generados son puntos de partida para revisión. Los tres archivos de entrega de AI-DLC incluyen el estado `requires_human_review`; sus responsables completan las decisiones antes de avanzar. Este comando prepara archivos sin ejecutar AWS.

## Inception: aceptar la oportunidad

1. Completar la [ficha de valor](FICHA_VALOR.md) con fuentes y marcar los supuestos. Comparar una alternativa manual, automatización sencilla, asistente de consulta y agente con escritura.
2. Definir usuario, resultado, autonomía, importe/datos permitidos y criterio de parada. Elegir una oportunidad no implica aceptar todas sus acciones.
3. Ejecutar A–C. Validar cada invariante con producto, operaciones y seguridad. Enlazar requisitos con los riesgos ARA/MODA cuando esos informes estén disponibles.
4. Registrar en `ai-dlc/decisions.md` la decisión, responsable, fecha, artefactos revisados y lo pendiente. Mantener las métricas comerciales en `por medir` hasta obtener datos.

**Prompt para el agente de desarrollo:**

> Lee la ficha de valor, el escenario, los contextos y el manifiesto de esta práctica. Propón requisitos y alternativas trazables al problema. Identifica los datos que faltan y las decisiones de autonomía que requieren validación humana. Conserva los supuestos como supuestos. Produce un plan de unidades de trabajo con criterios de aceptación observables y espera la decisión de los responsables antes de implementar.

## Construction: construir y comprobar

La primera unidad de trabajo del ejemplo es **crear una reserva aprobada sin duplicar sus efectos**. La segunda es **cancelarla con autorización y recuperación durable**. La tercera es **reconstruir lo ocurrido con evidencia**.

Para cada unidad:

1. Revisar la propuesta, la identidad del sujeto y el contrato de herramientas. Registrar qué decisión depende del usuario y qué puede resolver el agente.
2. Implementar el cambio en una rama. El [agente ejecutable](AGENTE_EJECUTABLE.md) tiene un planificador determinista para el recorrido reproducible y una integración Bedrock opcional; ambos desembocan en el mismo flujo de aprobación y herramientas permitidas.
3. Ejecutar pruebas unitarias y el E2E con PostgreSQL. Probar rechazo de aprobación, reintento, reinicio, identidad ajena y recuperación, además del caso exitoso.
4. Revisar el código y sus resultados de prueba. Para cerrar un hallazgo ARA/MODA, volver a evaluar la aplicación con el contexto y alcance definidos y comprobar la evidencia del control.
5. Actualizar `G-traceability.csv` y el registro de decisiones: requisito, cambio, prueba, responsable y medición de negocio pendiente.

### Aceptar una ejecución con un LLM real

Cuando una unidad de trabajo incluya el planificador Bedrock, verifica también sus propuestas con el modelo real. Necesitas Docker, AWS CLI y acceso al modelo en tu cuenta. Desde la raíz del repo:

```bash
python3 booking_lab/bedrock_e2e.py \
  --live-bedrock --confirm-test-operator \
  --model-id amazon.nova-micro-v1:0 --region us-east-1 \
  --output .local/bedrock-e2e.json
```

El recorrido realiza hasta cuatro inferencias: crear, consultar y cancelar con argumentos exactos, y rechazar una petición sin importe. Las escrituras exigen aprobación. La recuperación reutiliza el mismo plan sin volver a inferir ni cobrar. Una propuesta inesperada detiene la prueba.

`--confirm-test-operator` habilita un aprobador automatizado para los casos sintéticos exactos. Usa [la demo interactiva](AGENTE_EJECUTABLE.md) para revisar y aprobar cada propuesta personalmente. Las decisiones de producto se registran por separado en `ai-dlc/decisions.md`.

Usa un archivo de salida nuevo en cada ejecución. Revisa el resultado, las propuestas, la recuperación, la restauración y el cierre de recursos siguiendo la [referencia de verificación](AUDITORIA_E2E.md). La [guía de CloudShell](CLOUDSHELL.md) explica la preparación del entorno; la [evidencia publicada](evidence/bedrock/README.md) muestra los resultados del recorrido.

Mide después la calidad con usuarios, otras formulaciones, carga y costo por caso mediante el experimento definido en la ficha de valor.

**Prompt para el agente de desarrollo:**

> Trabaja en la unidad aprobada y enlaza cada cambio con su requisito. Muestra el plan y los archivos afectados. Conserva identidad, autorización, claves de idempotencia y estado durable. Implementa y ejecuta las pruebas de aceptación, incluidas las negativas. Entrega los cambios, comandos, resultados y riesgos pendientes. Marca un requisito como aprobado cuando su evidencia lo demuestre.

## Operations: operar el experimento y decidir

Asigna responsables de operación y define cómo medirás el resultado del piloto. Usa la recuperación y restauración del laboratorio como base para preparar el runbook de tu entorno.

- Operaciones conserva el JSON de ejecución, los tiempos y los incidentes. Los secretos y estados privados de sesión permanecen fuera de Git.
- Ingeniería comprueba que se desplegó el código probado. El operador comprueba recuperación, conciliación y cierre de recursos de la práctica.
- Producto mide la hipótesis con los usuarios y compara con la línea base usando la misma unidad y periodo.
- El equipo registra continuar, ajustar o detener, con dueño y fecha de revisión. Las brechas de modernización se convierten en trabajo explícito para el despliegue elegido.

**Prompt para el agente de desarrollo:**

> Reúne las evidencias del experimento y prepara un cierre operativo: estado del runtime, restauración, recursos de la práctica, métricas y responsables. Separa observaciones de hipótesis y tareas pendientes. Propón la siguiente decisión con referencias verificables. Conserva la aprobación humana para cambios de entorno y para aceptar el riesgo residual.

Continúa con la [guía de ejecución AWS](EJECUCION_AWS.md) para ARA/MODA. Conserva los artefactos de AI-DLC junto al código para que el equipo pueda retomar las decisiones y la medición de resultados.
