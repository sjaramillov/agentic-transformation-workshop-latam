# Validación E2E de la réplica MIT en CCS

El **16 de octubre de 2026, de 09:04:39 a 09:05:35 (America/Bogota)**, la implementación original de `booking_lab/` pasó **17 escenarios E2E con PostgreSQL 16.15**, dos instancias de API, un proveedor HTTP de pagos sintéticos y un worker de recuperación/auditoría. La ejecución terminó con código 0. Las contraseñas, tokens y datos de la cuenta AWS se mantienen fuera del repositorio.

La evidencia pública completa está en [evidence/db-e2e.json](evidence/db-e2e.json): casos y duraciones, imágenes resueltas por digest, hashes del código, resultado de restauración e invariantes finales. Cada hash de código se contrastó con el archivo local antes de publicar. El respaldo descargado desde CCS se verificó con SHA-256 `5e647216e55f64bd858615172394d8433d0d51b14a8b39c9ba8d2becd81aea3b`; conserva logs y dump sintético, excluyendo archivos `.env` y credenciales AWS.

## Cierre de las dos brechas

| Requisito pendiente | Corrección comprobada |
| --- | --- |
| AUTH-Q6: auditoría atribuible y durable | 35 eventos entregados con principal, correlación y operación; outbox transaccional; caída de permisos del destino y reinicio del worker; redelivery sin duplicados; roles de runtime sin UPDATE/DELETE sobre el registro de auditoría |
| STATE-Q1: compensar cobro si falla guardar la reserva | INSERT real rechazado por trigger después de cobrar; estado durable de compensación; reembolso idempotente; recuperación tras caída del proveedor o del proceso antes de registrar cobro/reembolso |

Estas brechas se resolvieron en el servicio original MIT. Los informes ARA/MODA del PHP anterior conservan sus hallazgos históricos. **No se ejecutó un nuevo análisis administrado de AWS sobre este código ni se modifica el número de bloqueadores de aquellos informes.** El cierre aquí corresponde a los requisitos y escenarios probados en la réplica original.

## Escenarios ejecutados

1. Token ausente, firma, issuer, audience, caducidad y scope incorrectos: escrituras rechazadas.
2. Crear, cobrar, persistir, consultar y listar una reserva con atribución comprobada en DB.
3. Repetir una petición entre instancias conserva la respuesta; cambiar el cuerpo con la misma clave produce conflicto.
4. Una identidad no consulta ni cancela reservas de otra; claves independientes por identidad.
5. Ocho solicitudes simultáneas contra dos APIs: una reserva y un cobro.
6. Fallo real de INSERT después del cobro: reembolso y ausencia de reserva huérfana.
7. Reembolso temporalmente caído: estado COMPENSATING persistido y recuperación del worker.
8. Muerte del proceso después del commit externo del cobro: reconciliación sin segundo cargo.
9. Caída del proveedor: intención persistida, respuesta 503 y recuperación posterior.
10. Muerte del proceso después del reembolso: cancelación recuperada sin segunda devolución.
11. Pago rechazado: no se crea la reserva.
12. Cancelación, reembolso y repetición; se preserva la respuesta original de creación.
13. Fallo real de permisos de entrega de auditoría, reinicio y drenaje del outbox.
14. Roles de runtime sin capacidad para reescribir auditoría, crear tablas o leer tablas de otro servicio según su rol.
15. Reentrega forzada: deduplicación por UUID de evento.
16. DB caída: liveness 200, readiness/escritura 503, ningún cobro nuevo; datos conservados tras reiniciar DB/APIs.
17. `pg_dump` restaurado en otra base; conteos y hashes de filas de seis tablas coinciden.

## Estado final comprobado

| Invariante | Conteo |
| --- | ---: |
| Cargos capturados sin reserva confirmada | 0 |
| Reservas confirmadas sin cargo capturado | 0 |
| Operaciones pendientes | 0 |
| Eventos sin entregar | 0 |
| Eventos sin atribución | 0 |
| Contenedores del test en ejecución al cierre | 0 |

La restauración contiene **7 reservas, 10 registros de pago y 35 eventos**. Estos son datos sintéticos del conjunto de pruebas, con estados confirmados, cancelados, compensados y rechazados. Los hashes del contenido de `operations`, `bookings`, `charges`, `outbox`, `audit_events` y `faults` coinciden entre origen y restauración.

## Repetición

```bash
python3 booking_lab/run.py e2e --output .local/db-e2e.json
```

Sigue [LABORATORIO_MIT.md](LABORATORIO_MIT.md) para requisitos, contrato de API, permisos y recuperación. CI ejecuta el mismo E2E en Linux y publica únicamente su JSON de evidencia. La suite local de herramientas/documentación pasó **26 pruebas, ninguna omitida**, al aportar la captura histórica; en CI la prueba que requiere esa captura se declara omitida.

## Alcance del resultado

Se validó un entorno Docker dentro de CCS con DB real y pagos sintéticos. No se conectó una pasarela financiera, no se movió dinero ni se desplegó un endpoint público. El emisor de tokens es un fixture local; para una instalación externa hay que integrar identidad y TLS. La auditoría está protegida contra los roles de runtime, no contra el administrador de PostgreSQL. La prueba del dump verifica datos; el bootstrap público reconstruye los permisos.

CloudShell no admitió los límites cgroup; la evidencia registra esa capacidad. Durante el desarrollo también se corrigieron la publicación de puertos sobre red interna, el lock compartido accidentalmente con el proveedor y la redetección de puertos después de reinicios. Los intentos fallidos se conservan en el respaldo privado; la evidencia pública identifica la ejecución final aprobada.
