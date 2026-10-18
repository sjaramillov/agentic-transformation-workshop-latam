# Validación de base de datos en CCS

**Registro histórico del 16 de octubre de 2026.** Esta página conserva los 18 casos y hashes de esa versión. El recorrido ampliado con agente y aprobación en servidor se documenta en [Auditoría E2E](AUDITORIA_E2E.md).

El código original MIT se prueba con PostgreSQL real, dos instancias de API, pagos sintéticos, un worker y un ledger independiente de auditoría. Todos los recursos de aplicación están en [booking_lab](booking_lab/README.md).

## Ejecución verificada

- Fuente pública: `401e5317567f3500843bc722893bf6d22b733390`; los hashes coinciden con los clones de ARA/MODA.
- CCS: **16 de octubre de 2026, 16:09:09–16:10:36 UTC**, PostgreSQL 16.15, **18/18 casos aprobados**, cinco invariantes en cero y cero contenedores activos al terminar. [JSON completo](evidence/mit/runtime/final-db-e2e-02.json).
- Auditoría: 35 eventos; manipulación y truncamiento detectados; reinicio y restauración verificados; administrador de la DB sin acceso al ledger independiente.
- Repetición en [GitHub Actions](https://github.com/sjaramillov/agentic-transformation-workshop-latam/actions/runs/38929875432): **18/18**, con [JSON publicado](evidence/mit/runtime/github-actions-db-e2e.json).
- Demo manual del mismo código en CCS: crear 201, listar 200, otro sujeto sin reservas, cancelar 200 y repetir sin duplicar. [Recibos completos](evidence/mit/runtime/manual-demo-verification.json). El runner terminó con `demo_stopped` y cero contenedores activos.

Se conserva también el [intento que falló](evidence/mit/runtime/final-db-e2e.json) por disco lleno en el driver Docker `vfs`. La limpieza de contenedores detenidos de esta práctica, conservando volúmenes y logs, recuperó 6.6 GiB; la corrida aceptada fue nueva. [Procedimiento reproducible](CLOUDSHELL.md).

## Reproducir

```bash
python3 -m unittest discover -s tests -v
python3 booking_lab/run.py e2e --output .local/db-e2e.json
```

La suite pública contiene pruebas de autenticación, integridad del ledger, preparación desde Git, herramientas y enlaces. El E2E verifica 18 escenarios:

1. Firma, issuer, audience, caducidad, activación, fechas finitas y scopes.
2. Crear, cobrar, persistir, consultar y listar con atribución.
3. Replay y conflicto de payload entre dos API.
4. Aislamiento entre identidades y claves por sujeto.
5. Ocho peticiones concurrentes producen una reserva y un cobro.
6. Fallo real de INSERT después del cobro obliga a reembolsar.
7. Caída del reembolso mantiene compensación durable y se recupera.
8. Caída del proceso después del cobro no duplica el cargo.
9. Caída del proveedor conserva intención y se recupera.
10. Caída después del refund no duplica devoluciones.
11. Pago rechazado no crea reserva.
12. Cancelación repetida conserva el replay original del POST.
13. Fallo de entrega de auditoría conserva outbox y recupera tras reiniciar.
14. Roles de runtime no reescriben auditoría ni tablas ajenas.
15. Redelivery deduplica eventos por UUID.
16. Caída de DB falla de forma cerrada y conserva datos tras reinicio.
17. `pg_dump` se restaura en otra base y compara seis tablas.
18. Ledger separado: firmas, cadena, checkpoint externo, manipulación, truncamiento, retención, reinicio y restauración SQLite.

El resultado debe contener `result: passed`, 18 casos aprobados, invariantes cero y cero contenedores de prueba ejecutándose. La [comparación ARA/MODA](CCS_E2E.md) enlaza la prueba con la versión de código evaluada.

## Qué demuestra cada almacén

PostgreSQL es el sistema de registro de operaciones, reservas, pagos y outbox. Su tabla `audit_events` es una proyección. El ledger independiente conserva el historial autoritativo; tiene volumen y clave separados y retención mínima de 90 días sin purga automática. [AUDIT.md](booking_lab/AUDIT.md) documenta la verificación y la frontera de confianza.

Los pagos son sintéticos. La evidencia incluye imágenes fijadas, hashes de fuente, resultados de restore y conteos; los secretos se conservan en archivos privados excluidos de Git. CloudShell observado no admite límites cgroup y el JSON registra esa capacidad.

La [prueba inicial de 17 escenarios](historico/CCS_DATABASE_E2E.md) queda disponible para comparar la evolución. Los informes de cada corrida deben conservarse por separado para evitar sobrescribir un fallo con un éxito.
