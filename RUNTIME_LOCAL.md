# Verificar el contenedor antes de aceptar la remediación

La ejecución de CCS del 16 de octubre de 2026 mostró que la primera TD puede terminar como `completed` y producir una imagen que compila, aunque el servicio falle:

| Prueba sobre la imagen generada | Resultado observado |
| --- | --- |
| `docker build` | Éxito |
| `php -l index.php` | Sin errores de sintaxis |
| `GET /` sin DB | HTTP 200 con error fatal `mysqli_sql_exception` |
| HEALTHCHECK original | `healthy` pese al error anterior |
| `GET /api/bookings` | 404 de Apache: no hay regla de entrada al PHP |
| `GET /.git/config` | HTTP 200: `COPY .` incluyó el repositorio en el directorio servido |

Las pruebas se hicieron con publicación del puerto **solo en `127.0.0.1`** y datos de laboratorio. No se desplegó EKS.

## Archivos originales para repetir la prueba

El ayudante [container_runtime_files.py](scripts/container_runtime_files.py) añade seis archivos a una copia PHP aislada. Rechaza sobrescribir archivos y conserva `index.php` tal cual. Incluye:

- `Dockerfile.runtime`: copia explícita de los tres PHP necesarios.
- `.dockerignore`: excluye Git, reportes y configuración local del contexto.
- `apache-workshop.conf`: enruta URLs hacia `index.php`, desactiva el listado de directorios y deniega rutas ocultas.
- `php-workshop.ini`: envía los errores al log sin devolver trazas al cliente.
- `health-live.php`: comprueba que PHP atiende peticiones.
- `health-ready.php`: devuelve 200 si puede hacer `SELECT 1`, o 503 sin exponer el error de conexión.

```bash
python3 scripts/container_runtime_files.py /ruta/a/copia/booking-service
cd /ruta/a/copia/booking-service
docker build -f Dockerfile.runtime -t booking-runtime:review .
docker run -d --name booking-runtime-review \
  -p 127.0.0.1:18081:80 booking-runtime:review
curl -i http://127.0.0.1:18081/health-live.php
curl -i http://127.0.0.1:18081/health-ready.php
curl -i http://127.0.0.1:18081/.git/config
```

Sin DB, se espera **200 / 503 / 403**, respectivamente. Estos tres resultados se observaron en CCS tras reconstruir la imagen corregida; `/api/bookings` pasó a llegar a PHP y respondió 500 por la DB ausente. No uses `healthy` como prueba de readiness: la salud del proceso y la conexión a la DB son controles distintos. En Kubernetes, asigna las rutas correspondientes a `livenessProbe` y `readinessProbe`. Con DB disponible falta validar el esquema, los endpoints de negocio y sus fallos.

La imagen base conserva `php:8.2-apache` del ejercicio; el digest de base observado fue `sha256:06617d90f29b57b2aa200a9df03b3bafbfa5c66d2e2913fbb2b5f775a8358465`. Registra el digest resuelto y revisa soporte y vulnerabilidades antes de un uso posterior. El ayudante corrige el empaquetado para pruebas, **no implementa autenticación M2M, idempotencia correcta, compensación durable ni una plataforma AWS desplegable**. Los criterios restantes están en [LIMITACIONES_TD.md](LIMITACIONES_TD.md).

## Espacio y limpieza acotada

La segunda construcción en CloudShell agotó el volumen raíz de 16 GiB y devolvió `no space left on device`. Revisa `df -h /`, `docker system df` y el espacio de tu entorno antes de construir; tener 1 GiB de almacenamiento personal no garantiza espacio suficiente para las capas Docker.

La limpieza de tres registros concretos de la caché propia y de la imagen intermedia liberó 2.2 GiB. El contador lógico de caché mostraba pocos KiB, por lo que en este entorno no era una estimación fiable del espacio físico recuperable.

Conserva evidencias antes de retirar los contenedores de tu prueba. Evita limpiezas globales en entornos compartidos. Docker permite seleccionar registros concretos de caché con [buildx prune y su filtro id](https://docs.docker.com/reference/cli/docker/buildx/prune/).

## Regresión del callback de idempotencia

[probe_shutdown_order.php](scripts/probe_shutdown_order.php) ejecuta el PHP transformado con una clase `mysqli` falsa, usando `php -n` para desactivar la extensión real. Simula un DELETE y falla si el callback intenta persistir la respuesta después de cerrar la conexión. **Solo prueba el orden de esas operaciones; no prueba SQL, concurrencia ni una base de datos.**

```bash
php -n scripts/probe_shutdown_order.php /ruta/a/copia/booking-service/index.php
```

Un resultado satisfactorio debe tener exit code 0 y el marcador `PROBE_RESPONSE_PERSISTENCE_REACHED`. Si falta el marcador, la prueba no acredita persistencia. No publiques este archivo como un endpoint web.

En CCS la salida original de la segunda TD produjo el error `response persistence attempted after connection close`. Se retiró el cierre prematuro al final del PHP y se dejó que PHP libere la conexión después de los callbacks. El mismo probe terminó con exit code 0 y el marcador esperado. Para aplicar exactamente esa corrección en otra copia compatible:

```bash
python3 scripts/fix_shutdown_order.py /ruta/a/copia/booking-service/index.php
php -n scripts/probe_shutdown_order.php /ruta/a/copia/booking-service/index.php
```

El ayudante verifica el patrón observado, rechaza versiones distintas y registra hashes antes/después. Esta corrección no resuelve la delimitación de la clave por identidad/operación, su recuperación tras fallos ni la atomicidad entre el efecto de negocio y su registro de idempotencia.
