# Verificar el workshop

Ejecuta estos comandos desde la raíz del repositorio. Los [resultados publicados](evidence/bedrock/README.md) permiten consultar la evidencia técnica.

## 1. Código, materiales y flujo con PostgreSQL

Con Python 3.11+ y Docker activo:

```bash
python3 -m unittest discover -s tests -v
python3 booking_lab/run.py e2e --output .local/db-e2e.json
```

La suite unitaria debe terminar en `OK`. El E2E usa el planificador determinista y comprueba aprobación, aislamiento por usuario, idempotencia, recuperación, auditoría y restauración con una base real y pagos sintéticos.

## 2. Agente con Bedrock real

Necesitas también AWS CLI y acceso al modelo en tu cuenta. Esta prueba invoca Bedrock y genera consumo AWS:

```bash
python3 booking_lab/bedrock_e2e.py \
  --live-bedrock --confirm-test-operator \
  --model-id amazon.nova-micro-v1:0 --region us-east-1 \
  --output .local/bedrock-e2e.json
```

Usa un archivo de salida nuevo para cada ejecución. El recorrido exige tres propuestas exactas —crear, consultar y cancelar— y un rechazo por importe ausente, con cuatro respuestas de modelo. Una propuesta inesperada detiene la prueba; no activa el planificador determinista.

`--confirm-test-operator` aprueba automáticamente solo los casos sintéticos esperados. Para revisar y aprobar propuestas personalmente, usa la [demo del agente](AGENTE_EJECUTABLE.md).

El emisor de aprobación está controlado por el operador del laboratorio. Un despliegue productivo requiere autenticar al aprobador y separar ese emisor del proceso del agente.

## 3. Comprueba el resultado

| Control | Resultado esperado |
| --- | --- |
| Ejecución | Código de salida 0, `result: passed` y todos los casos aprobados |
| Aprobación e identidad | Ninguna escritura sin aprobación válida; cada usuario accede a sus reservas |
| Recuperación | Reutilizar el mismo plan y clave; un solo cobro y un solo reembolso por operación |
| Restauración | `snapshot_barrier.result: passed`, escritores detenidos y colas vacías antes del backup; comparación de seis tablas aprobada |
| Estado final | Ninguna operación o evento pendiente, ni cobros o reembolsos duplicados; auditoría íntegra |
| Cierre | `cleanup.result: passed`, `cleanup.unknown_count: 0` y `test_containers_running: 0` |

Consulta [el runtime](RUNTIME_LOCAL.md) para resolver problemas del entorno y [CloudShell](CLOUDSHELL.md) para la ejecución en AWS.

ARA/MODA se ejecutan con la [guía de AWS Transform](EJECUCION_AWS.md). Para aceptar valor de negocio, mide con usuarios la línea base, el resultado y los costos definidos en la [ficha de valor](FICHA_VALOR.md), y registra la decisión en [AI-DLC](AI_DLC.md).
