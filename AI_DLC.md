# Integrar el workshop en AI-DLC

**Objetivo:** convertir una oportunidad de negocio en requisitos, cambios revisables y evidencia que permita decidir el siguiente paso. El agente de desarrollo propone planes y artefactos; las personas responsables aceptan la intención, el alcance y las decisiones críticas.

AWS organiza AI-DLC en **Inception**, **Construction** y **Operations**, con contexto acumulado y validación humana. La tabla siguiente es la adaptación de este repositorio a esas fases, basada en la [descripción oficial de AI-DLC](https://aws.amazon.com/blogs/devops/ai-driven-development-life-cycle/).

## Un recorrido, tres entregas

| Fase | Entrada | Actividad del workshop | Artefactos de salida | Responsable y condición para avanzar |
| --- | --- | --- | --- | --- |
| **Inception** | Problema, evidencia del proceso y alternativas | Ficha de valor; EventStorming A; oportunidad B; autonomía C; lectura inicial ARA/MODA D–F | Hipótesis, métricas, límites, requisitos y unidades de trabajo | Producto acepta problema/objetivo y alternativa; seguridad acepta el límite de autonomía. Sin línea base, registrar una tarea de medición |
| **Construction** | Requisitos aceptados, contexto y hallazgos comprobados | Priorización G; cambios H; agente con aprobación; pruebas de DB y comparación I | Diff revisado, pruebas, trazabilidad y decisiones técnicas | Ingeniería revisa; seguridad verifica identidad/aprobación; aceptación técnica ligada al comportamiento y commit |
| **Operations** | Artefactos y resultados del mismo commit | Recuperación, restauración, observación y cierre J; medición de valor | Recibo de ejecución, incidencias, runbook, dueño y decisión de continuar | Operaciones acepta recuperación; producto revisa resultados. Un despliegue productivo exige su propia infraestructura y validación |

ARA/MODA pueden repetirse durante las tres fases cuando cambian código, contexto o alcance. Aportan hallazgos a los requisitos y a las decisiones; no sustituyen la ficha de valor ni la aceptación del comportamiento. Las pruebas del backend tampoco establecen por sí mismas la calidad de un planificador con LLM.

## Preparar los artefactos de una práctica

Desde un clon público:

```bash
python3 scripts/workshop.py prepare --output .local/workshop-01
```

El preparador toma **un mismo commit** para aplicación, escenario, contextos y plantillas. Registra hashes de entradas y entregables en `manifest.json`, además del hash del script preparador utilizado. Si necesitas repetir una versión, usa `--revision` con su SHA público. Los cambios sin commit no forman parte de esa instantánea.

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

Los archivos generados son puntos de partida para revisión; los tres handoffs JSON de AI-DLC incluyen el estado `requires_human_review`. Crearlos no aprueba decisiones ni ejecuta AWS. Las revisiones anteriores a la incorporación de estos materiales conservan sus artefactos originales; el manifiesto indica qué entregables estaban disponibles.

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
4. Revisar el diff y las evidencias del mismo commit. Si se repite ARA/MODA, conservar contexto, alcance, IDs, versión del CLI y hashes. Comparar por pregunta y verificar los hallazgos antes de decidir.
5. Actualizar `G-traceability.csv` y el registro de decisiones. Un control implementado puede quedar `pendiente de reevaluación ARA` sin alterar el informe histórico.

**Prompt para el agente de desarrollo:**

> Trabaja en la unidad aprobada y enlaza cada cambio con su requisito. Muestra el plan y los archivos afectados. Conserva identidad, autorización, claves de idempotencia y estado durable. Implementa y ejecuta las pruebas de aceptación, incluidas las negativas. Entrega diff, comandos, resultado, commit y riesgos pendientes; no marques aprobado un requisito sin evidencia correspondiente.

## Operations: operar el experimento y decidir

El laboratorio opera contenedores y datos sintéticos, conserva recibos y prueba restauración. La infraestructura productiva, el proveedor de identidad externo, la supervisión sostenida y los resultados con usuarios pertenecen al entorno de destino.

- Operaciones conserva el JSON de ejecución, los tiempos y los incidentes. Los secretos y estados privados de sesión permanecen fuera de Git.
- Ingeniería comprueba que la versión desplegada corresponde a la versión probada. El operador comprueba recuperación, conciliación y cierre de recursos de la práctica.
- Producto mide la hipótesis con los usuarios y compara con la línea base usando la misma unidad y periodo.
- El equipo registra continuar, ajustar o detener, con dueño y fecha de revisión. Las brechas de modernización se convierten en trabajo explícito para el despliegue elegido.

**Prompt para el agente de desarrollo:**

> Reúne las evidencias de esta versión y prepara un cierre operativo: estado del runtime, restauración, recursos de la práctica, incidentes, métricas y responsables. Separa observaciones de hipótesis y tareas pendientes. Propón la siguiente decisión con referencias verificables. Conserva la aprobación humana para cambios de entorno y para aceptar el riesgo residual.

## Qué evidencia demuestra cada afirmación

| Afirmación | Evidencia necesaria |
| --- | --- |
| Se reprodujo el flujo técnico | Recibo E2E, casos/invariantes y hashes de la versión |
| El agente respeta una aprobación concreta | Pruebas negativas de la API y del agente, más prueba positiva sobre DB |
| Un planificador Bedrock funcionó | Recibo de una llamada real, modelo/región y resultado revisado; los tests con respuestas simuladas cubren el contrato |
| Se cerró un hallazgo ARA/MODA | Informe nuevo del mismo alcance y revisión de la evidencia; el informe histórico mantiene su fecha y commit |
| Se obtuvo valor para el negocio | Línea base y resultados medidos con usuarios, costos y guardas de calidad |
| Se puede operar en producción | Diseño, despliegue y validación específica del entorno aceptados por sus responsables |

La guía de [ejecución AWS](EJECUCION_AWS.md), la [comparación histórica](CCS_E2E.md) y la [evidencia pública](evidence/mit/README.md) permiten continuar el ciclo con fuentes visibles. El equipo conserva sus artefactos de AI-DLC junto al código para que la siguiente sesión pueda reconstruir decisiones y resultados.
