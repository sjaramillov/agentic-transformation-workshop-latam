# Ejecutar el laboratorio con Docker y PostgreSQL

Necesitas Python 3.11+ y Docker activo en Linux, macOS, WSL o AWS CloudShell. Desde la raíz del repositorio:

```bash
python3 booking_lab/run.py e2e --output .local/db-e2e.json
```

El [runner](booking_lab/run.py) usa imágenes fijadas en [images.lock.json](booking_lab/images.lock.json). Para conversar con el agente y aprobar sus propuestas, sigue la [demo interactiva](AGENTE_EJECUTABLE.md).

## Qué se crea

- PostgreSQL con un volumen exclusivo y roles separados.
- Dos instancias API, un proveedor de pagos sintéticos, un worker y un servicio de auditoría.
- Una red interna para DB/pagos y otra para publicar la API en loopback.
- Archivos privados por ejecución en `.local/db-lab-<id>/`.

La API corre como usuario no root, sin capabilities, con sistema de archivos de solo lectura y tmpfs. El runner aplica límites de CPU, memoria y procesos cuando el daemon declara las tres capacidades. El recibo registra `resource_limit_capabilities` y si se aplicaron esos límites.

## Si necesitas resolver un problema

| Si ocurre | Qué hacer |
| --- | --- |
| Docker no responde | Inicia el daemon y comprueba `docker info`. En AWS, sigue la preparación de [CloudShell](CLOUDSHELL.md). |
| Falta espacio al descargar imágenes o repetir la práctica | Revisa el almacenamiento disponible. Sigue la limpieza de CloudShell para retirar únicamente recursos de tu práctica que ya no necesites. |
| El recibo indica `resource_limits_available: false` | Consulta `resource_limit_capabilities`. Para probar los tres límites, utiliza un host que los soporte. |
| El agente queda `pending` después de una interrupción | Recupera el servicio y repite `execute` con el mismo archivo de estado, según [la guía del agente](AGENTE_EJECUTABLE.md). |
| Una prueba falla | Consulta el caso indicado en el JSON y sus logs en el directorio privado. Corrige la causa y conserva el resultado antes de repetir. |
| El cierre informa errores o estados desconocidos | Revisa los contenedores identificados en `cleanup.containers`; detén e inspecciona cada recurso de esa práctica. El cierre está completo cuando todos están detenidos. |

## Resultado esperado

El proceso termina con código 0 y el JSON contiene `result: passed`, todos los casos aprobados, invariantes en cero y `cleanup.result: passed`. El cierre exige `cleanup.unknown_count: 0` y `test_containers_running: 0`.

La prueba drena las colas, detiene los escritores y restaura un backup en otra base para comparar seis tablas. Al terminar conserva contenedores detenidos, volumen, dump y archivos privados para revisión. La [referencia de verificación](AUDITORIA_E2E.md) explica los controles y enlaza la evidencia pública.

El laboratorio usa una sola instancia PostgreSQL y pagos sintéticos. Para operar un servicio público, define identidad, TLS, observabilidad y recuperación en el entorno de destino.
