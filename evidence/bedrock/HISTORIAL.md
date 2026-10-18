# Agente con Bedrock real y PostgreSQL en CCS

Esta validación usa el transporte AWS CLI `bedrock-runtime converse` del agente público. La ejecución real se registra por separado de la [validación determinista](../agent-workshop/README.md).

## Resultado observado el 18 de octubre de 2026

Se ejecutó el código público desde un clon limpio en **AWS CloudShell CCS**, con PostgreSQL **16.15** y **Amazon Nova Micro `amazon.nova-micro-v1:0` en `us-east-1`**. El primer intento expuso un rechazo incorrecto del modelo; el segundo y el tercero completaron **7/7 casos con cuatro inferencias reales cada uno**. La ejecución final incorpora la verificación estricta del cierre de los seis contenedores.

| Ejecución | Fuente | Resultado | Inferencias |
| --- | --- | --- | --- |
| [01: antes de corregir](bedrock-live-01.json) | `62a990e` | Tres casos pasaron; consulta rechazada; cancelación/restauración no alcanzadas | 3 respuestas completas |
| [02: instrucciones por acción y muestreo](bedrock-live-02.json) | `8831425` | 7/7 casos aprobados | 4 respuestas completas: 3 planes exactos y 1 rechazo esperado |
| [03: aceptación final y cierre comprobado](bedrock-live-03.json) | `aa7bb87` | 7/7 casos; 6/6 contenedores detenidos con inspección exitosa | 4 respuestas completas: 3 planes exactos y 1 rechazo esperado |

### Qué falló y qué cambió

Nova respondió `{"action":"unsupported"}` a «Consulta y muestra mis reservas actuales sin modificarlas». Se aclararon por separado los requisitos de consulta, creación y cancelación, y se fijó `temperature=0.00001`. Se repitieron las mismas peticiones de importe ausente, creación y consulta; el ID de cancelación se obtiene de cada nueva reserva sintética. Cambiaron tanto las instrucciones como la configuración de muestreo: esta comparación no aísla el efecto de uno solo de ellos.

El segundo intento verificó creación sin efectos antes de aprobar, caída/reanudación del proveedor sin otra inferencia ni doble cobro, consulta por sujeto, cancelación con nueva aprobación, un solo reembolso y restauración de seis tablas. Terminó con una reserva cancelada, un pago reembolsado, cinco registros de auditoría firmados y cero operaciones o eventos pendientes.

La revisión posterior encontró que el cierre anterior no distinguía una inspección Docker fallida de un contenedor detenido. Una [inspección independiente](bedrock-cleanup-02.json) confirmó que los seis contenedores de la ejecución 02 estaban detenidos. El commit `aa7bb87` corrige el runner y añade trece regresiones. La ejecución 03 pasó con `cleanup.result: passed`, seis inspecciones exitosas, cero estados desconocidos y cero contenedores activos. Las **112 pruebas unitarias** pasaron también dentro de CCS.

### Alcance de la evidencia

Los recibos registran commit limpio, hashes de 17 archivos, imágenes, objetivos sintéticos, acciones validadas, hashes de los recibos de inferencia, uso/latencia informados por el servicio y resultados de DB. El [preflight](ccs-bedrock-preflight.json) documenta acceso al modelo y entorno; no sustituye el E2E.

- Las inferencias invocan AWS CLI Converse real; el proveedor de pagos es sintético y no mueve dinero.
- La recuperación reutiliza el estado persistido; no pide al modelo otra decisión.
- El CLI no expuso el request ID: se conserva `null`. Los recibos y hashes permiten trazabilidad del ensayo; no son una atestación independiente del proveedor.
- CloudShell no confirmó límite de memoria de Docker; `resource_limits_available` es falso. La práctica conserva aislamiento de red, filesystem y capabilities; no constituye una prueba de límites de memoria.
- La prueba usa un aprobador de fixture explícito. La evaluación de calidad general, costo en producción y valor de negocio necesita su propio experimento.
- Esta ejecución no vuelve a ejecutar ARA/MODA ni modifica sus informes históricos.

## Archivos y comprobaciones

- [Verificación de hashes y resultados](verification.json): tres ejecuciones reales, 51 hashes de fuente y 11 recibos de inferencia cotejados; incluye tiempos, uso de tokens y origen de CI.
- [Incidentes y correcciones](incidents.json): rechazo observado de consulta y hallazgo de revisión del cierre.
- [CI del mismo código `aa7bb87`](https://github.com/sjaramillov/agentic-transformation-workshop-latam/actions/runs/39133062523): **6/6 trabajos aprobados**, 112 pruebas en Linux/macOS y Python 3.11/3.14, más dos E2E de PostgreSQL.
- [E2E determinista 1](database-e2e-1.json) y [E2E determinista 2](database-e2e-2.json): **28/28 casos cada uno**, hashes del mismo código y cierre verificado. Estas ejecuciones de CI no invocan Bedrock.
- [SHA256SUMS](SHA256SUMS): integridad de los JSON descargados y los resúmenes derivados. Las guías posteriores pueden tener otro commit; los recibos conservan el commit exacto del runtime ejecutado.

Desde la raíz del clon, comprueba los archivos publicados:

```bash
shasum -a 256 -c evidence/bedrock/SHA256SUMS
```

Se conservaron los tres intentos, con **11 inferencias en total**: 3 en el intento fallido y 4 en cada ejecución completa. El runner no reintentó una respuesta para buscar una favorable. Las repeticiones siguieron cambios de código identificados. Los logs privados y sesiones quedan fuera de Git; el código completo, las instrucciones y estos recibos están publicados.

## Repetir la prueba

Desde un clon público, con Python 3.11+, Docker, AWS CLI y credenciales autorizadas:

```bash
LAB_EVIDENCE_ENV='AWS CloudShell CCS' python3 booking_lab/bedrock_e2e.py \
  --live-bedrock --confirm-test-operator \
  --model-id amazon.nova-micro-v1:0 --region us-east-1 \
  --output .local/bedrock-live-01.json
```

El runner admite como máximo cuatro inferencias, con un intento del CLI y hasta 512 tokens de salida cada una. Exige la selección explícita del modelo/región y del aprobador de prueba. Conserva cualquier fallo, detiene sus propios contenedores y rechaza un destino de evidencia existente. No utiliza `rules` cuando falla Bedrock.

Para probar manualmente las decisiones, sigue [Agente ejecutable](../../AGENTE_EJECUTABLE.md). La [guía de CloudShell](../../CLOUDSHELL.md) explica preparación, almacenamiento y limpieza de recursos de la práctica.

## Contrato de aceptación

- Una petición sin importe devuelve exactamente la propuesta no soportada; no basta con JSON malformado o un error de acceso.
- Crear, consultar y cancelar producen las acciones y parámetros esperados antes de aprobar escrituras.
- Ejecutar sin aprobación no modifica la base. La aprobación de creación no autoriza cancelar.
- Una caída real del proveedor permite reanudar el mismo plan sin otra inferencia ni doble cobro.
- La cancelación aprobada produce un solo reembolso; la repetición conserva el recibo.
- La restauración compara seis tablas después de drenar colas y detener escritores; la auditoría conserva integridad.
- El cierre exige parada e inspección exitosas para cada contenedor; un error o estado desconocido hace fallar el resultado.

Las confirmaciones son de un operador de pruebas sobre pagos sintéticos. Este ejercicio no acredita una identidad humana independiente, calidad general del modelo ni impacto de negocio medido.

## Fuentes de la integración

[Converse en AWS CLI](https://docs.aws.amazon.com/cli/latest/reference/bedrock-runtime/converse.html) y [Amazon Nova Micro](https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-amazon-nova-micro.html). La [configuración de inferencia de Nova](https://docs.aws.amazon.com/nova/latest/userguide/complete-request-schema.html) documenta el mínimo de temperatura de `0.00001`; no garantiza respuestas deterministas. Disponibilidad y acceso deben comprobarse en cada cuenta y región.
