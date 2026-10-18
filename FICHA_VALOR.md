# Elegir una oportunidad y comprobar su valor

**Resultado de este ejercicio:** una decisión explicable sobre qué construir, qué autonomía permitir y qué evidencia exigir. Producto y operaciones completan la ficha antes de pedir al agente de desarrollo que implemente cambios.

Usa la [plantilla vacía](workshop/templates/value.md) y la [matriz de trazabilidad](workshop/templates/traceability.csv). El [escenario público](workshop/scenario.json) contiene el ejemplo resuelto en formato estructurado. `scripts/workshop.py prepare` genera una copia editable de ambos para cada práctica.

## Ejemplo resuelto: reservas recuperables

**Contexto didáctico:** una persona ayuda al viajero a registrar y cancelar reservas. Las respuestas ambiguas pueden provocar reintentos, consultas manuales y conciliaciones. El backend permite reproducir esos fallos con pagos sintéticos y comprobar su recuperación.

**Decisión que se quiere informar:** ¿conviene introducir un asistente que prepare la operación y la ejecute después de una aprobación explícita, o basta con mejorar el formulario y la automatización determinista?

**Hipótesis:** preparar la propuesta y consultar automáticamente su resultado podría reducir el tiempo humano por caso completado, conservando el control sobre importe, itinerario y cancelación.

### Supuestos para practicar la decisión

Los valores son **supuestos ilustrativos**. Sustitúyelos por datos de tu organización.

| Campo | Ejemplo editable | Estado |
| --- | --- | --- |
| Usuario | Operador que asiste a un viajero | Escenario sintético |
| Frecuencia | 200 casos al mes | Supuesto pedagógico |
| Línea base | 8 minutos de trabajo humano por caso completado | Supuesto pedagógico |
| Objetivo | 6 minutos por caso, incluida revisión y recuperación | Hipótesis; reducción del 25% respecto al supuesto |
| Beneficio bruto de tiempo | `200 × (8 − 6) = 400 minutos/mes` (6 h 40 min) | Estimación ilustrativa; aún sin costo de operación |
| Calidad | Ningún cobro duplicado ni escritura sin aprobación | Guarda de aceptación; medir también fuera del laboratorio |
| Esfuerzo | Implementación, revisión, mantenimiento y formación | Por estimar con el equipo |
| Costos | Modelo, runtime, almacenamiento, observabilidad y errores | Por medir; usar unidades y factura/estimación fechada |
| Responsable | Producto acepta valor; operaciones mide tiempos; ingeniería y seguridad verifican controles | Roles que cada equipo debe asignar |

Los seis minutos por caso ya incluyen revisión y recuperación: no restes ese tiempo una segunda vez. Para estimar beneficio neto añade el esfuerzo de implementación y mantenimiento y los costos incrementales de operación, usando unidades compatibles. Convertir tiempo disponible en dinero requiere un valor por hora explícito y una justificación de cómo se aprovechará esa capacidad.

### Comparar alternativas antes de elegir

| Alternativa | Qué permite comprobar | Motivo para elegirla |
| --- | --- | --- |
| Procedimiento manual mejorado | Efecto de instrucciones más claras | El problema principal es confusión operativa |
| Formulario con automatización determinista | Captura validada, aprobación e idempotencia | Las entradas y decisiones son estructuradas |
| Asistente de consulta | Explicación del estado sin modificar reservas | El valor está en localizar y entender información |
| Agente con aprobación | Interpretar una intención, proponer, ejecutar y observar | La flexibilidad de entrada mejora el resultado medido frente a las alternativas |

El workshop permite ejercitar la cuarta alternativa con el [agente ejecutable](AGENTE_EJECUTABLE.md). Su modo determinista permite estudiar el contrato sin un modelo; el planificador Bedrock opcional permite experimentar con interpretación de lenguaje. Ambos usan las mismas restricciones y aprobación.

### Límites y parada

- Datos, importes, identidades y pagos sintéticos; acciones limitadas a crear, consultar y cancelar reservas propias.
- Aprobación de cada escritura ligada a la propuesta concreta. Una modificación exige revisión nueva.
- Una respuesta ambigua exige consultar o reintentar con la identidad y clave originales, conservando el estado de ejecución.
- Detener el experimento ante escritura sin aprobación, cruce de identidad, cobro duplicado, exposición de un secreto o resultado imposible de reconciliar. Conservar evidencia y asignar el incidente.
- Define límites de gasto, delegación e identidad para el entorno donde realizarás el piloto.

## Del riesgo al comportamiento comprobable

La siguiente tabla enlaza requisitos con nombres exactos de escenarios del [runner de DB](booking_lab/run.py). Guarda el resultado de tus pruebas junto con la versión del código.

| ID | Consecuencia de negocio | Control y prueba técnica | Medición de negocio pendiente |
| --- | --- | --- | --- |
| R1 | Un reintento podría duplicar un cobro | Idempotencia: `eight_concurrent_requests_two_api_replicas_one_charge` | Tasa de cobros duplicados por caso completado |
| R2 | Un cobro sin reserva genera conciliación y reclamos | Compensación: `real_insert_failure_after_charge_refunds_without_orphan`; recuperación: `refund_outage_durable_state_and_worker_recovery` | Casos pendientes de conciliación y minutos humanos de resolución |
| R3 | Un sujeto podría consultar o cancelar reservas ajenas | Autorización: `identity_isolation_and_identity_scoped_idempotency` | Incidentes de acceso cruzado; guarda de parada |
| R4 | Sería difícil reconstruir una operación controvertida | Auditoría: `independent_signed_audit_retention_tamper_restart_restore` | Tiempo hasta reconstruir un caso con evidencia verificable |
| R5 | Una aprobación ambigua permitiría una operación no deseada | Rechazo sin efectos: `agent_cli_plan_unapproved_execute_and_rejection_have_no_writes`; validación de la API: `server_approval_missing_expired_subject_payload_key_action_signature_denied` | Escrituras no deseadas, rechazos y tiempo de revisión |

ARA ayuda a identificar riesgos para la interacción con agentes; MODA identifica brechas de modernización. Su [alcance técnico documentado](https://docs.aws.amazon.com/transform/latest/userguide/transform-aws-customs.html) aporta evidencia a esta decisión. El resultado comercial requiere medir el proceso y sus usuarios.

Las preguntas `STATE-Q1`, `AUTH-Q6`, `HITL-Q1` y `HITL-Q2` de la evaluación histórica ayudan a relacionar controles con riesgos. Los cambios posteriores al commit evaluado deben someterse a una nueva evaluación para atribuirles un resultado ARA/MODA. La [comparación fechada](CCS_E2E.md) conserva esa identidad.

## Cómo medir en un piloto propio

1. Registrar la línea base real antes de fijar el objetivo: casos completados, tiempo humano total, errores, recuperación y costo por caso.
2. Elegir casos equivalentes y alternar el orden de trabajo manual/asistido para reducir el efecto de aprendizaje. Separar casos sencillos y casos con fallos. Determinar participantes y duración según la variabilidad observada.
3. Registrar el mismo inicio/fin, unidad y denominador en ambos recorridos. Incluir revisión, rechazo y recuperación; conservar también casos fallidos.
4. Comparar tiempo, calidad y costo. El umbral didáctico del 25% puede reemplazarse, pero debe quedar acordado antes de observar los resultados.
5. Producto y operaciones deciden continuar, ajustar, preferir una alternativa más sencilla o detener. Anotar la evidencia y las condiciones de revisión.

El laboratorio valida comportamientos técnicos. El piloto con usuarios valida la hipótesis de valor. Conserva ambos resultados en la matriz de trazabilidad y entrégalos al siguiente ciclo de [AI-DLC](AI_DLC.md).
