# Booking Lab — código original MIT

Desde la raíz del repositorio:

```bash
python3 booking_lab/run.py e2e --output .local/db-e2e.json
```

Requisitos: Python 3.11+, Docker y acceso al daemon. La guía completa, el contrato de API, las garantías y los comandos para CCS están en [LABORATORIO_MIT.md](../LABORATORIO_MIT.md).

- `service.py`: API, saga durable, worker y proveedor HTTP de pagos sintéticos.
- `schema.sql`: esquema, permisos de roles separados y fallos de DB administrados por el test.
- `auth.py`: emisor y verificador de tokens locales para los fixtures.
- `agent.py`: controlador de objetivos, propuesta, aprobación, herramientas y recuperación; planificador determinista y adaptador Bedrock opcional.
- `approval.py`: capacidad de aprobación firmada y vinculada a la operación; el servidor la exige para escribir.
- `http_safety.py`: transporte directo sin proxies del entorno ni redirecciones para pagos y auditoría.
- `run.py`: creación aislada del entorno y aceptación E2E con DB real.
- `requirements.txt`, `images.lock.json`, `Dockerfile`: versiones e imágenes fijadas.

Para una sesión interactiva usa `python3 booking_lab/run.py demo --output .local/demo.json` y sigue [Agente ejecutable](../AGENTE_EJECUTABLE.md). El cliente `client.py` también exige aprobar cada escritura. Para ARA/MODA sigue [Ejecución AWS](../EJECUCION_AWS.md).


## Security and audit changes

Creation requires `bookings:write`; cancellation requires the independent `bookings:cancel` scope. All reads are constrained to the authenticated subject. The operator fixture issues five-minute tokens and rejects non-finite or boolean NumericDate values.

The authoritative audit ledger is a separate process and volume with append-only endpoints, SHA256 chaining and HMAC signatures. See [AUDIT.md](AUDIT.md) for retention, externally retained checkpoints, tamper detection and the trust boundary. PostgreSQL `audit_events` is a query projection. The E2E includes real PostgreSQL recovery and an independent audit restore.
