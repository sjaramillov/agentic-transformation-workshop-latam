# Laboratorio completo de reservas, pagos y auditoría

Esta implementación original, incluida bajo MIT, permite repetir el ejercicio desde un clon público. Requiere **Python 3.11+, Git y Docker Engine** con acceso al daemon; usa PostgreSQL real y dos instancias de una API Python. El simulador HTTP de pagos guarda cargos y reembolsos en PostgreSQL; todos los importes y las identidades son sintéticos.

## Ejecutar desde cero

En Linux, macOS con Docker o AWS CloudShell con Docker disponible:

```bash
git clone https://github.com/sjaramillov/agentic-transformation-workshop-latam.git
cd agentic-transformation-workshop-latam
python3 booking_lab/run.py e2e --output .local/db-e2e.json
```

No necesitas la captura del evento, instalar paquetes Python en el host, crear IAM, configurar Bedrock ni aprovisionar RDS/EKS. Docker instala dentro de la imagen la dependencia fijada en [requirements.txt](booking_lab/requirements.txt). Las imágenes están fijadas por digest en `booking_lab/images.lock.json` y el Dockerfile. La primera ejecución las descarga e instala esa dependencia; reserva al menos 4 GiB de disco libre y 1.5 GiB de memoria para una corrida. En Docker con driver `vfs`, limpia los contenedores detenidos de la corrida anterior antes de repetir, siguiendo [CloudShell](CLOUDSHELL.md). La configuración exacta observada se conserva en la evidencia.

**Éxito:** el proceso termina con código 0, cada caso imprime `PASS`, `result` es `passed` y todas las invariantes de `.local/db-e2e.json` valen cero. Un fallo termina con código distinto de cero y conserva los logs. No cambies las aserciones para aceptar un fallo.

El runner crea nombres únicos, descubre puertos libres y publica la API en `127.0.0.1`. PostgreSQL y pagos están en una red Docker interna sin puertos publicados. Usa contraseñas aleatorias y credenciales distintas por servicio; los archivos `.env` privados tienen modo 0600. Al terminar detiene únicamente sus contenedores y conserva el volumen, el dump y los logs en `.local/db-lab-*/` para revisión. Repetir el comando crea un laboratorio nuevo. No publica tokens, contraseñas ni identificadores AWS en la evidencia.

## Explorar el servicio manualmente

Para el recorrido con planificación, aprobación y recuperación usa primero el [agente ejecutable](AGENTE_EJECUTABLE.md). El cliente de operador de esta sección también pide aprobación antes de crear o cancelar; ambos llaman al mismo contrato de API.

En una primera terminal inicia la demo:

```bash
python3 booking_lab/run.py demo --output .local/demo.json
```

Espera `DEMO_READY`. Copia la ruta `session=...` en una segunda terminal del mismo host. Esa sesión es un fixture privado del operador del laboratorio; el cliente genera tokens efímeros y nunca los imprime.

```bash
export DEMO_SESSION=/ruta/mostrada/session.json
python3 booking_lab/client.py --session "$DEMO_SESSION" create --key reserva-001
python3 booking_lab/client.py --session "$DEMO_SESSION" list
python3 booking_lab/client.py --session "$DEMO_SESSION" --subject agent-b list
# Copia el id de la reserva de agent-a:
python3 booking_lab/client.py --session "$DEMO_SESSION" cancel ID_DE_RESERVA
```

Antes de cada escritura el cliente muestra la acción y pide `APROBAR <digest>`. Repite `create` con la misma clave y cuerpo para observar el replay. Cambia `--amount` con la misma clave y aprueba esa propuesta para recibir 409. La lista de agent-b no muestra reservas de agent-a. Termina con Ctrl+C en la primera terminal; los contenedores se detienen y sus datos quedan disponibles para revisión. La demo es interactiva; el comando `e2e` produce la evidencia automatizada.

## Integridad y atribución

| Brecha | Implementación original | Prueba |
| --- | --- | --- |
| AUTH-Q6: atribución y durabilidad | Token firmado validado; principal y correlación persistidos; evento outbox en la misma transacción que el cambio; entrega idempotente a ledger independiente firmado y proyección PostgreSQL; runtime sin UPDATE/DELETE | Identidad cruzada rechazada, evento atribuible, permiso de entrega retirado, reinicio del worker, cola drenada y redelivery sin duplicados |
| STATE-Q1: cobro seguido de fallo de reserva | Intención guardada antes del cobro, clave estable en el proveedor, estado COMPENSATING persistido, refund idempotente y reconciliador | Trigger PostgreSQL hace fallar realmente el INSERT después del cobro; no queda reserva ni cargo huérfano; reembolso caído se recupera; proceso muerto después del cobro no duplica cargos y proceso muerto después del reembolso no duplica devoluciones |

La reserva, su respuesta de idempotencia y su evento se confirman en una transacción PostgreSQL. El cobro es una transacción externa del simulador: no se supone una transacción distribuida ni se promete entrega exactamente una vez. La recuperación y las claves idempotentes resuelven reintentos. Un fallo ambiguo de COMMIT exige volver a leer el estado antes de reembolsar.

```mermaid
flowchart LR
  A[Agente con token y clave] --> B[Guardar intención + evento]
  B --> C[Proveedor: cobrar una sola vez]
  C --> D{Guardar reserva}
  D -->|OK| E[Reserva + respuesta + outbox]
  D -->|Falla SQL| F[Persistir COMPENSATING]
  F --> G[Reembolso idempotente]
  G --> H[COMPENSATED + evento]
  F -. reintento del worker .-> G
  B -. recuperación tras caída .-> C
  E --> I[Worker de auditoría]
  H --> I
  I --> J[Ledger independiente: cadena + firma + retención]
  J --> K[Proyección PostgreSQL + confirmación del outbox]
```

## Contrato de la API

| Método y ruta | Scope | Resultado |
| --- | --- | --- |
| GET `/health/live` | Público local | Proceso atiende |
| GET `/health/ready` | Público local | DB y tabla de operaciones accesibles; 503 si fallan |
| POST `/bookings` | `bookings:write` | `{"itinerary":"BOG-MDE","amount":12500}`; requiere `Idempotency-Key` y `X-Booking-Approval`; 201 al confirmar |
| GET `/bookings` | `bookings:read` | Solo reservas del principal autenticado |
| GET `/bookings/{id}` | `bookings:read` | Detalle propio o 404 |
| DELETE `/bookings/{id}` | `bookings:cancel` | Requiere su propia `X-Booking-Approval`; cancelación y reembolso idempotente |

`amount` es entero en unidades mínimas de la moneda del laboratorio. Una clave se delimita por principal y operación; el cuerpo se canoniza y compara por hash. Cambiar el cuerpo con la misma clave da 409. La misma solicitud enviada en paralelo a dos instancias produce una reserva y un cobro. Se conserva la respuesta original del POST después de cancelar; GET muestra el estado actual.

El emisor del laboratorio firma tokens HS256 de cinco minutos con clave aleatoria. La API comprueba firma, algoritmo, issuer, audience, caducidad, activación y scope; no tiene un modo de autenticación desactivada. Este emisor es un fixture local. Una integración externa requiere un proveedor de identidad, gestión de claves, TLS e ingress apropiados. El servidor HTTP de Python es un runtime didáctico; la prueba en CloudShell no certifica exposición pública ni alta disponibilidad.

Además, la API exige una aprobación firmada para cada escritura. [approval.py](booking_lab/approval.py) vincula sujeto, método, ruta, hash del payload y clave idempotente, con vigencia máxima de cinco minutos y clave distinta a JWT. Una autorización ausente, vencida, alterada o dirigida a otra operación devuelve 403 antes de crear intención/cobro. La sesión del operador es el emisor didáctico; la prueba acredita el vínculo de la capacidad y la decisión en la CLI, no identidad independiente de un aprobador. Las llamadas HTTP de cliente, pagos y auditoría rechazan redirecciones y no heredan proxies del sistema.

## Revisar la evidencia y continuar

[booking_lab/run.py](booking_lab/run.py) deja la lista de casos, versiones, digests de imágenes resueltos, hashes del código, resultado de restauración y conteos finales. [schema.sql](booking_lab/schema.sql) permite revisar permisos y restricciones, y [service.py](booking_lab/service.py) contiene la saga y el outbox.

El archivo `review.json` privado identifica el prefijo del laboratorio y sus puertos. Los logs y el dump contienen solo los datos sintéticos de la ejecución. Las credenciales de los archivos `.env` son locales y no deben subirse a Git. Guarda el directorio privado si necesitas retomar la sesión. Para volver a probar desde cero utiliza el comando inicial; no hace falta borrar un laboratorio anterior.

El registro de auditoría autoritativo vive en un servicio y volumen separados, con cadena de hashes y firmas HMAC; PostgreSQL conserva una proyección consultable. El administrador de la DB de reservas no recibe el volumen ni la clave del ledger. La retención, verificación y frontera de confianza están descritas en [AUDIT.md](booking_lab/AUDIT.md). El outbox conserva eventos durante una caída del destino; una caída permanente requiere intervención operativa. El reconciliador debe ejecutarse para resolver estados pendientes, y las garantías del proveedor real deben verificarse antes de sustituir el simulador.

La evaluación ARA/MODA del **16 de octubre de 2026**, previa al nuevo agente y la aprobación verificada por la API, se conserva en [CCS_E2E.md](CCS_E2E.md). La [auditoría vigente](AUDITORIA_E2E.md) enlaza la aceptación técnica del recorrido ampliado. Para repetir los análisis sigue [Ejecución AWS](EJECUCION_AWS.md); el preparador crea las fuentes desde el código público y conserva commit y hashes.

## Compatibilidad comprobada con CloudShell

CloudShell puede informar que su kernel no admite límites cgroup de CPU, memoria y PIDs. El runner registra `resource_limits_available: false` y mantiene las restricciones de usuario, capabilities, filesystem y red de los contenedores de aplicación. En hosts con las tres capacidades aplica esos límites. La API usa una red de entrada y otra red interna hacia DB/pagos: publicar puertos directamente sobre una red `--internal` no produjo bindings en el Docker de CloudShell.

Los volúmenes Docker residen en el almacenamiento del daemon; no presupongas que sobreviven al reciclado de CloudShell. El E2E demuestra persistencia tras reiniciar la DB y restaura un `pg_dump` en una DB distinta, comparando conteos y hashes de todas las filas de seis tablas. Descarga el dump si necesitas conservar datos más allá de la sesión. Esa restauración de datos no reconstruye permisos: para una instalación nueva ejecuta también el bootstrap de roles y el esquema.

Referencias técnicas: [transacciones de Psycopg](https://www.psycopg.org/psycopg3/docs/basic/transactions.html), [bloqueos PostgreSQL](https://www.postgresql.org/docs/16/explicit-locking.html), [pg_dump](https://www.postgresql.org/docs/16/app-pgdump.html) e [instalación del adaptador](https://www.psycopg.org/psycopg3/docs/basic/install.html).

Los locks de la saga usan la variante PostgreSQL de una clave bigint; el proveedor usa la variante de dos enteros, que tiene un espacio independiente. Compartir el mismo lock entre quien llama y quien recibe la llamada produjo un bloqueo observado durante el desarrollo y se corrigió antes de aceptar la ejecución.

Los puertos asignados por Docker pueden cambiar al reiniciar un contenedor. El runner descubre los puertos nuevamente después de los reinicios; `review.json` conserva los últimos observados.
