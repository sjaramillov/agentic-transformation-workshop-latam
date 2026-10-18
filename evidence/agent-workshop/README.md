# Validación del workshop con agente, valor y AI-DLC

**18 de octubre de 2026 — resultado aprobado.** Código de aplicación y pruebas: [`926265a55a301c8d54e64876fd28a34c50208e94`](https://github.com/sjaramillov/agentic-transformation-workshop-latam/commit/926265a55a301c8d54e64876fd28a34c50208e94).

| Comprobación | Resultado | Evidencia |
| --- | --- | --- |
| CI de la revisión | 5/5 trabajos aprobados | [GitHub Actions 39129820064](https://github.com/sjaramillov/agentic-transformation-workshop-latam/actions/runs/39129820064) |
| Suite pública | 76 pruebas; matriz Linux/macOS y Python 3.11/3.14 aprobada | Trabajos `public-checks` de la misma ejecución |
| Agente + API + PostgreSQL 16.15 | **28/28 escenarios E2E**, incluidos nueve recorridos CLI | [Recibo completo](database-e2e.json) |
| Invariantes | Cinco en cero; cero contenedores de prueba activos al terminar | Recibo completo |
| Auditoría | 52 eventos; integridad y restauración PostgreSQL/SQLite comprobadas | `independent_audit` y `restored_table_row_hashes` del recibo |
| Identidad del código | Los 16 archivos de `booking_lab/` coinciden por SHA256 con el commit probado | [Verificación](verification.json) |
| Clon público nuevo | 76 pruebas aprobadas, sin paquete privado; 16 entregables preparados con hashes coincidentes | [Recibo del clon](public-clone.json) |
| Artefactos didácticos visibles | Ejemplo generado del mismo commit, con decisiones humanas pendientes | [Ejemplo completo](../../examples/workshop/README.md) |

El E2E se ejecutó en **GitHub Actions, Ubuntu**, de `13:02:40` a `13:03:41 UTC` (61 segundos observados, incluido montaje y cierre). Ese tiempo pertenece a esta corrida y no es una estimación para otros hosts. Las comprobaciones de clon público se realizaron en macOS con Python 3.14.0.

El archivo `database-e2e.json` es el artefacto de CI conservado byte a byte. `verification.json` registra su SHA256, el commit, los trabajos y la comparación de nombres de casos extraídos del runner con los efectivamente ejecutados. Los hashes identifican los archivos; la ejecución de los escenarios aporta la evidencia de comportamiento.

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
