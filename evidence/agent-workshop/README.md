# Validación del workshop con agente, valor y AI-DLC

**18 de octubre de 2026 — resultado aprobado.** Código de aplicación y pruebas: [`9e028a85a381f68374fdfa121c70d4114811d1ac`](https://github.com/sjaramillov/agentic-transformation-workshop-latam/commit/9e028a85a381f68374fdfa121c70d4114811d1ac).

| Comprobación | Resultado | Evidencia |
| --- | --- | --- |
| CI de la revisión | 6/6 trabajos aprobados | [GitHub Actions 39130821144](https://github.com/sjaramillov/agentic-transformation-workshop-latam/actions/runs/39130821144) |
| Suite pública | 86 pruebas; matriz Linux/macOS y Python 3.11/3.14 aprobada | Trabajos `public-checks` de la misma ejecución |
| Agente + API + PostgreSQL 16.15 | **28/28 escenarios E2E en dos ejecuciones independientes**, incluidos nueve recorridos CLI | [Repetición 1](database-e2e.json) y [repetición 2](database-e2e-repeat.json) |
| Invariantes | Cinco en cero; cero contenedores de prueba activos al terminar, en ambas corridas | Ambos recibos |
| Auditoría | 52 eventos por corrida; integridad y restauración PostgreSQL/SQLite comprobadas | `independent_audit` y `restored_table_row_hashes` de ambos recibos |
| Backup estable | Cuatro escritores detenidos y dos colas vacías antes de `pg_dump`; seis tablas restauradas con hashes iguales | `snapshot_barrier` y `restored_table_row_hashes` |
| Límites Docker | Memoria, CPU y procesos confirmados y activados en ambos entornos | `resource_limit_capabilities` y `resource_limits_available` |
| Identidad del código | Los 16 archivos de `booking_lab/` coinciden por SHA256 con el commit probado | [Verificación](verification.json) |
| Clon público nuevo | 86 pruebas aprobadas, sin paquete privado; 16 entregables preparados con hashes coincidentes | [Recibo del clon](public-clone.json) |
| Artefactos didácticos visibles | Ejemplo generado del mismo commit, con decisiones humanas pendientes | [Ejemplo completo](../../examples/workshop/README.md) |

El E2E se ejecutó en **dos runners independientes de GitHub Actions, Ubuntu**. La primera repetición fue de `13:16:33` a `13:17:33 UTC`; la segunda, de `13:16:31` a `13:17:27 UTC`, el 18 de octubre. Son tiempos observados de estas corridas, incluido montaje y cierre, no estimaciones para otros hosts. El clon público se comprobó en macOS con Python 3.14.0.

Los archivos `database-e2e.json` y `database-e2e-repeat.json` conservan los artefactos de CI byte a byte. `verification.json` registra sus SHA256, el commit, los seis trabajos y los nombres de casos contrastados con el runner. Los hashes identifican los archivos; los escenarios aportan evidencia de comportamiento.

## Fallo encontrado y corregido

La repetición anterior detectó una carrera: `pg_dump` conservó 50 eventos y el worker agregó dos antes de comparar la base activa, que ya tenía 52. Ahora el runner detiene ambas API, drena operaciones y auditoría, detiene worker y pagos, y comprueba que no queden escritores ni pendientes antes del backup. Mantiene las comparaciones estrictas de conteos y hashes de las seis tablas.

También se corrigió `CPUCfsQuota` por el campo real `CpuCfsQuota` de Docker; el valor falso de corridas antiguas no demostraba falta de soporte del host. Hay diez pruebas de regresión nuevas sobre la barrera y las capacidades. Consulta [incidentes y correcciones](incidents.json), el [recibo fallido conservado](runs/39130162323-database-e2e.json) y la [primera corrida aprobada](runs/39129820064-database-e2e.json). Los recibos históricos no se reescribieron.

## Qué se comprobó en el agente

Se invocó la CLI en procesos independientes contra HTTP y PostgreSQL reales del laboratorio: planificar sin efectos; rechazar sin efectos; aprobar y crear; consultar; denegar otro sujeto y un plan alterado; serializar dos CLI sobre un estado; recuperar caída del proveedor y del proceso API después del cobro; retirar aprobación sin perder una operación enviada; cancelar con aprobación nueva y reembolsar una vez.

La API rechazó capacidades ausentes, vencidas, alteradas o vinculadas a otro sujeto, cuerpo, clave o método antes de producir efectos. Las regresiones unitarias incluyen respuestas ajenas, proxies de entorno y redirecciones, expiración, bloqueo concurrente y salidas de modelo inválidas.

## Alcance de esta evidencia

- El planificador ejecutado en el E2E fue **`rules`**. La integración Bedrock se comprobó con respuestas controladas del CLI; **no hubo una inferencia real** en esta validación.
- Las confirmaciones E2E son decisiones explícitas de un operador de prueba. Las claves del emisor didáctico no acreditan una identidad humana independiente.
- La ficha incluye supuestos de valor y un diseño de medición. No se midieron ahorro, ROI ni resultados de usuarios.
- No se ejecutaron nuevos ARA/MODA en esta ampliación. Los [informes del 16 de octubre](../../CCS_E2E.md) conservan su código, resultados y riesgos; no se atribuyen cierres nuevos a esos informes.
- El entorno usa pagos e identidades sintéticos. La aceptación corresponde al contrato de la práctica y a los fallos ejercitados.

## Repetir

Desde un clon de la revisión que quieras comprobar:

```bash
python3 -m unittest discover -s tests -v
python3 booking_lab/run.py e2e --output .local/agent-db-e2e.json
python3 scripts/workshop.py prepare --output .local/agent-practice --revision HEAD
```

Conserva commit, hashes, salida y resultado de tu corrida. Un nuevo estado del agente representa una intención nueva; para reanudar, sigue [Agente ejecutable](../../AGENTE_EJECUTABLE.md) y conserva su archivo original.

## Validación posterior con Bedrock real

La [ejecución específica de Bedrock en CCS](../bedrock/README.md) conserva sus propios recibos, commits y fallo corregido. Los resultados y el alcance `rules` de este directorio permanecen como evidencia fechada.
