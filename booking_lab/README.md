# Booking Lab — código original MIT

Desde la raíz del repositorio:

```bash
python3 booking_lab/run.py e2e --output .local/db-e2e.json
```

Requisitos: Python 3.11+, Docker y acceso al daemon. La guía completa, el contrato de API, las garantías y los comandos para CCS están en [LABORATORIO_MIT.md](../LABORATORIO_MIT.md).

- `service.py`: API, saga durable, worker y proveedor HTTP de pagos sintéticos.
- `schema.sql`: esquema, permisos de roles separados y fallos de DB administrados por el test.
- `auth.py`: emisor y verificador de tokens locales para los fixtures.
- `run.py`: creación aislada del entorno y aceptación E2E con DB real.
- `requirements.txt`, `images.lock.json`, `Dockerfile`: versiones e imágenes fijadas.

Los casos no requieren AWS Transform. Para estudiar ARA/MODA, analiza este servicio como un repositorio propio y conserva sus resultados por separado de los informes históricos del PHP.
