# Runtime reproducible: Docker y PostgreSQL

El runtime se implementa en [booking_lab/run.py](booking_lab/run.py), con imágenes fijadas en [images.lock.json](booking_lab/images.lock.json). El mismo comando sirve en Linux con Docker, macOS con Docker y CloudShell con Docker disponible:

```bash
python3 booking_lab/run.py e2e --output .local/db-e2e.json
```

## Qué se crea

- PostgreSQL con un volumen exclusivo y roles separados.
- Dos instancias API, un proveedor de pagos sintéticos y un worker.
- Una red interna para DB/pagos y otra para los puertos de API publicados en loopback.
- Archivos privados por ejecución en `.local/db-lab-<id>/` con permisos restringidos.

La API corre como usuario no root, sin capacidades, con sistema de archivos de solo lectura y tmpfs. Los límites de CPU/memoria/PID se aplican cuando el daemon los soporta. CloudShell observado no los soporta; el resultado lo registra.

## Fallos reproducidos y corregidos durante la construcción

| Fallo | Corrección incorporada | Evidencia |
| --- | --- | --- |
| CloudShell rechaza límites cgroup | Detectar capacidades antes de pasar flags | `resource_limits_available` en el JSON |
| Red interna sin puerto de host utilizable | Red de entrada separada, publicación solo en loopback | Pruebas HTTP de ambas API |
| Bloqueo entre pago y reserva | Namespaces distintos de advisory locks | Concurrencia y recuperación E2E |
| El puerto cambia tras reiniciar | Redescubrir bindings después de restart | Escenarios de caída de proceso y DB |
| Servidor temporal de init se confunde con DB lista | Comprobar TCP y permisos antes de arrancar API | Preparación y prueba de permisos |

## Aceptación

El JSON debe contener `result: passed`, todos los casos aprobados, invariantes cero y `test_containers_running: 0`. Se conserva un dump sintético y se restaura realmente en otra base, comparando filas de seis tablas. [CCS_DATABASE_E2E.md](CCS_DATABASE_E2E.md) describe la evidencia inicial; [CCS_E2E.md](CCS_E2E.md) documenta el ciclo nuevo de análisis y correcciones.

La arquitectura del ejercicio usa una sola instancia de PostgreSQL. Las garantías probadas cubren los fallos inyectados y la restauración documentada; un despliegue público requiere su identidad, TLS, observabilidad y política de recuperación operativa.
