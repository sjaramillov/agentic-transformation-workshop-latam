# Agente de reservas: proponer, aprobar y ejecutar

Ejecuta una reserva, consulta el resultado y cancélala con una aprobación nueva. El agente guarda cada intención para poder reanudarla si falla un servicio. Todo el código está en [agent.py](booking_lab/agent.py), bajo MIT; los pagos son **sintéticos**.

Necesitas Python 3.11+, Docker y dos terminales en el mismo host. Usa Linux, macOS o WSL con Docker accesible. Ejecuta los comandos desde la raíz del repositorio.

| Planificador | Entrada | Requisito adicional |
| --- | --- | --- |
| `rules`, predeterminado | `create BOG-MDE 12500`, `list`, `cancel ID` | Ninguno; funciona sin AWS |
| `bedrock`, opcional | Objetivo en lenguaje natural | AWS CLI, credenciales y acceso al modelo elegido; genera consumo AWS |

## 1. Inicia la aplicación

En la primera terminal:

```bash
python3 booking_lab/run.py demo --output .local/demo.json
```

Espera `DEMO_READY session=...` y deja esa terminal abierta. En la segunda, copia la ruta que mostró el programa:

```bash
export DEMO_SESSION=/ruta/mostrada/session.json
```

La demo inicia PostgreSQL, API, proveedor de pagos sintéticos, recuperación y auditoría. **Mantén privados la sesión y el directorio `.local/`: contienen claves y archivos de la práctica.**

## 2. Crea una reserva

```bash
python3 booking_lab/agent.py --session "$DEMO_SESSION" \
  --state .local/reserva-001.json --goal 'create BOG-MDE 12500' run
```

Revisa sujeto, itinerario e importe: `12500` son unidades mínimas sintéticas. Para autorizar la propuesta, escribe la frase completa `APROBAR <digest>` que muestra el programa. La aprobación dura cinco minutos. Cualquier otra respuesta rechaza esta propuesta inicial sin enviarla.

**Resultado esperado:** JSON con `status: completed` y la reserva observada. Usa un archivo de estado nuevo para cada operación nueva.

## 3. Consulta y cancela

```bash
python3 booking_lab/agent.py --session "$DEMO_SESSION" \
  --state .local/consulta-001.json --goal list run

# Sustituye ID_DE_RESERVA por el ID devuelto en la consulta.
python3 booking_lab/agent.py --session "$DEMO_SESSION" \
  --state .local/cancelacion-001.json --goal 'cancel ID_DE_RESERVA' run
```

Consultar no pide aprobación. Revisa el ID antes de aprobar la cancelación: debe terminar en `CANCELLED`, con un reembolso sintético. Una consulta nueva permite ver el estado actual; repetir un estado completado devuelve su recibo guardado.

## 4. Reanuda si hay un problema

| Salida | Qué hacer |
| --- | --- |
| `completed` · código `0` | La operación terminó. Crea una consulta nueva si necesitas su estado actual. |
| `pending` · código `3` | Recupera el servicio y repite `execute` con **el mismo archivo de estado**. |
| `needs_approval` · código `2` | Revisa la propuesta con `inspect`, confirma con `approve` y repite `execute`. |
| `rejected`, `failed` o error de validación · código `2` | Revisa el mensaje. No edites el JSON de estado para forzar su aceptación. |

```bash
python3 booking_lab/agent.py --session "$DEMO_SESSION" --state .local/reserva-001.json inspect
python3 booking_lab/agent.py --session "$DEMO_SESSION" --state .local/reserva-001.json approve
python3 booking_lab/agent.py --session "$DEMO_SESSION" --state .local/reserva-001.json execute
```

Ante una respuesta perdida, conserva el estado original: crear otro archivo puede crear otra reserva. Retirar la aprobación con `reject` después de un envío no deshace una operación aceptada por el servidor; consulta el resultado y, si corresponde, cancela con una propuesta nueva.

También puedes separar los pasos desde el inicio: usa `plan` en lugar de `run`, seguido de `inspect`, `approve` y `execute`.

## 5. Usa Bedrock para interpretar el objetivo

Elige un modelo o inference profile compatible con [Converse](https://docs.aws.amazon.com/cli/latest/reference/bedrock-runtime/converse.html), disponible en tu cuenta y región. Necesitas permiso `bedrock:InvokeModel`; las inferencias generan consumo AWS.

```bash
export BEDROCK_MODEL_ID=amazon.nova-micro-v1:0
export AWS_REGION=us-east-1
python3 booking_lab/agent.py --session "$DEMO_SESSION" \
  --state .local/bedrock-001.json --planner bedrock \
  --model-id "$BEDROCK_MODEL_ID" --region "$AWS_REGION" \
  --planner-evidence .local/bedrock-001-planner.json \
  --goal 'Propón una reserva BOG-MDE por 12500 unidades sintéticas' run
```

Revisa y aprueba la propuesta como en el paso 2. El modelo recibe el objetivo y las acciones permitidas; las claves de la sesión permanecen en el controlador. Si la inferencia falla o la propuesta es inválida, corrige el problema antes de volver a planificar. El agente no cambia automáticamente a `rules`.

Usa nombres nuevos para el estado y el recibo de cada propuesta Bedrock. Para reanudar una operación ya propuesta, usa `execute` con su estado original: no necesitas otra inferencia.

## 6. Valida el flujo completo

### Sin llamadas a un modelo

```bash
python3 -m unittest discover -s tests -v
python3 booking_lab/run.py e2e --output .local/agent-db-e2e.json
```

**Resultado esperado:** pruebas aprobadas, `result: passed` en el JSON y `test_containers_running: 0`.

### Con Bedrock real y PostgreSQL

Este comando crea su propio laboratorio; no necesita la demo abierta:

```bash
python3 booking_lab/bedrock_e2e.py \
  --live-bedrock --confirm-test-operator \
  --model-id amazon.nova-micro-v1:0 --region us-east-1 \
  --output .local/bedrock-live-01.json
```

Realiza hasta cuatro inferencias para rechazar una reserva sin importe, crear, consultar y cancelar. También comprueba recuperación ante una caída del proveedor, un solo cobro/reembolso, auditoría y restauración de PostgreSQL. `--confirm-test-operator` autoriza al runner a aprobar automáticamente solo las propuestas exactas del caso de prueba; para aprobarlas tú, usa el paso 5.

**Resultado esperado:** siete casos aprobados, `result: passed`, `cleanup.result: passed` y `test_containers_running: 0`. Usa **un archivo de salida nuevo por corrida**; se rechazan destinos existentes. Consulta los [resultados de referencia](evidence/bedrock/README.md) o los [criterios técnicos de validación](AUDITORIA_E2E.md) si necesitas profundizar.

## Cierra la práctica

Termina la demo con Ctrl+C en su primera terminal. Los runners detienen sus contenedores y conservan los datos privados para revisión. Si necesitas liberar espacio, sigue la [limpieza de CloudShell](CLOUDSHELL.md#5-guarda-resultados-y-libera-espacio).

Registra el resultado en la [ficha de valor](FICHA_VALOR.md) y continúa con la [integración AI-DLC](AI_DLC.md).
