# Agente de reservas: proponer, aprobar, ejecutar y recuperar

Este agente de workflow convierte un objetivo en una acción permitida, muestra una propuesta, obtiene aprobación para escribir, llama a la API y observa el resultado. Conserva su intención en disco para reanudar después de una interrupción. Todo el código está en [agent.py](booking_lab/agent.py) bajo MIT.

| Planificador | Entrada | Requisitos | Qué se evalúa |
| --- | --- | --- | --- |
| `rules` — predeterminado | `create BOG-MDE 12500`, `list`, `cancel ID` | Python 3.11+ y el laboratorio Docker | Flujo determinista reproducible con DB y herramientas HTTP reales; no invoca un LLM |
| `bedrock` — opcional | Objetivo en lenguaje natural | AWS CLI, credenciales y un modelo compatible elegido por ti | El LLM propone una acción; el mismo controlador valida, pide aprobación y ejecuta |

La suite habitual `booking_lab/run.py e2e` utiliza `rules`. La [validación del 18 de octubre](evidence/agent-workshop/README.md) conserva ese alcance y sus pruebas de contrato del adaptador Bedrock con respuestas controladas. La sección 7 permite ejecutar una validación distinta con inferencias reales y recibo propio; sus resultados se consultan en [evidencia Bedrock](evidence/bedrock/README.md).

## 1. Inicia la aplicación

En una terminal, desde la raíz del repo:

```bash
python3 booking_lab/run.py demo --output .local/demo.json
```

Espera `DEMO_READY session=...`. Mantén esa terminal abierta y copia la ruta exacta en otra terminal del mismo host:

```bash
export DEMO_SESSION=/ruta/mostrada/session.json
```

El runner crea PostgreSQL, dos réplicas API, pagos sintéticos, recuperador y auditoría. La sesión privada contiene claves de laboratorio y permisos de archivo 0600. El agente usa HTTP en loopback y no envía esas claves al planificador.

## 2. Propón una reserva y decide

```bash
python3 booking_lab/agent.py --session "$DEMO_SESSION" \
  --state .local/reserva-001.json --goal 'create BOG-MDE 12500' run
```

Revisa sujeto, itinerario e importe: `12500` son unidades mínimas **sintéticas**, sin transferencia de dinero. Copia la frase completa `APROBAR <digest>` que muestra el programa para autorizar esa propuesta durante cinco minutos. Cualquier otra respuesta, incluido Enter o fin de entrada, la rechaza sin escribir en la API.

La salida JSON muestra `status: completed` solo cuando se recibió y observó el resultado esperado. `result.observed` conserva la observación del servidor cuando existe. Un estado completado guarda el recibo de esa ejecución; usa una consulta nueva para conocer cambios posteriores.

## 3. Consulta y cancela con una aprobación nueva

```bash
python3 booking_lab/agent.py --session "$DEMO_SESSION" \
  --state .local/consulta-001.json --goal list run

# Sustituye ID_DE_RESERVA por el ID de la consulta anterior.
python3 booking_lab/agent.py --session "$DEMO_SESSION" \
  --state .local/cancelacion-001.json --goal 'cancel ID_DE_RESERVA' run
```

Consultar es una herramienta de lectura. Cancelar necesita otra propuesta y otra aprobación vinculadas al ID exacto. El agente no puede convertir una aprobación de creación en una cancelación. Para observar aislamiento entre sujetos, consulta con `--subject agent-b` y un archivo de estado nuevo.

## 4. Separa planificación, aprobación y ejecución

```bash
python3 booking_lab/agent.py --session "$DEMO_SESSION" \
  --state .local/reserva-002.json --goal 'create BOG-MDE 12500' plan
python3 booking_lab/agent.py --session "$DEMO_SESSION" \
  --state .local/reserva-002.json inspect
python3 booking_lab/agent.py --session "$DEMO_SESSION" \
  --state .local/reserva-002.json approve
python3 booking_lab/agent.py --session "$DEMO_SESSION" \
  --state .local/reserva-002.json execute
```

`plan` prepara una intención sin llamar a la API. `approve` pide confirmación; `reject` retira la aprobación y termina la propuesta si aún no hubo intentos. Después del primer intento conserva el seguimiento, como se explica en recuperación. `execute` necesita una aprobación vigente para cualquier escritura. La API comprueba además la capacidad firmada: sujeto, método, ruta, hash del cuerpo, clave idempotente y vencimiento deben coincidir. Arrancar la API exige una clave de aprobación distinta de la de autenticación.

La sesión es un **emisor didáctico controlado por el operador**. Quien posee sus claves puede emitir capacidades: esta frontera demuestra validación de una aprobación concreta, sin establecer identidad independiente de un aprobador humano. Un servicio operado requiere separar ese emisor y su autenticación del proceso del agente.

## 5. Recupera una respuesta ambigua

| Salida | Significado | Próximo paso |
| --- | --- | --- |
| `0` y `completed` | Resultado observado o recibo completado recuperado | Consultar si necesitas el estado actual |
| `3` y `pending` | Fallo temporal o respuesta ambigua | Repetir `execute` sobre **el mismo archivo** después de recuperar el servicio |
| `2` y `needs_approval` | Aprobación ausente, vencida o retirada después de un intento | Consultar si hubo un envío previo; revisar, ejecutar `approve` y repetir `execute` con el mismo archivo |
| `2` y `rejected` / `failed`, o error de validación | Rechazo humano, error terminal o estado inválido | Revisar la causa; un estado alterado no se acepta |

El controlador persiste antes de llamar a una herramienta y realiza un intento acotado por comando. En una reanudación consulta el estado del servidor y conserva sujeto, payload, correlación y clave. No crea automáticamente otra intención ni renueva una aprobación vencida.

Retirar la aprobación después de un intento detiene nuevas escrituras del agente, pero el servidor puede haber aceptado la operación y su worker puede completarla. Ese estado queda `needs_approval` y señala `remote_operation_may_continue`; consulta el estado real y, si corresponde, cancela con una nueva aprobación. Renovar la aprobación de la intención original permite reconciliarla con la misma clave. Rechazar antes del primer intento sí termina sin enviar la operación.

Crear un archivo nuevo representa **otra operación**. Ante una respuesta perdida, conserva el archivo original: una clave nueva puede producir otra reserva. El estado se escribe atómicamente con modo 0600, sello HMAC y bloqueo de proceso; no contiene claves ni tokens. La implementación usa `fcntl` y está comprobada en Linux/macOS; en Windows utiliza WSL con Docker accesible.

## 6. Usa un modelo Bedrock opcional

Configura credenciales en tu entorno autorizado y elige un modelo o inference profile compatible con Converse. La operación requiere `bedrock:InvokeModel`; consulta la [referencia oficial de AWS CLI](https://docs.aws.amazon.com/cli/latest/reference/bedrock-runtime/converse.html). La cuenta, región, disponibilidad y costos pertenecen a tu ejecución.

```bash
export BEDROCK_MODEL_ID=ID_O_PERFIL_DISPONIBLE_EN_TU_CUENTA
export AWS_REGION=us-east-1
python3 booking_lab/agent.py --session "$DEMO_SESSION" \
  --state .local/bedrock-001.json --planner bedrock \
  --model-id "$BEDROCK_MODEL_ID" --region "$AWS_REGION" \
  --planner-evidence .local/bedrock-001-planner.json \
  --goal 'Propón una reserva BOG-MDE por 12500 unidades sintéticas' run
```

Se envían únicamente el objetivo y el esquema permitido. El modelo puede proponer `list`, `create` o `cancel`; no elige identidad, URL, cabeceras, código ni permisos. JSON inválido, campos adicionales, importes inválidos y acciones desconocidas se rechazan. Una falla del modelo termina sin ejecutar una escritura ni cambiar silenciosamente de planificador. La propuesta siempre necesita revisión humana antes de escribir, incluso si tiene estructura válida.

`--planner-evidence` crea un recibo JSON privado adicional, con modo 0600. Registra modelo/región, tiempos, hashes del objetivo, prompt de sistema y respuesta, estado de validación, código de salida del CLI y los tokens/latencia que devuelva Bedrock. Conserva `request_id: null` si el CLI no expone ese dato. No incluye claves ni el stderr de AWS. El archivo debe ser nuevo y distinto de la sesión y del estado; la opción se usa con `plan` o `run` y planificador `bedrock`. Revisa el recibo antes de publicarlo.

## 7. Ejecuta el E2E con Bedrock real y PostgreSQL

Este recorrido necesita AWS CLI, Docker, Python 3.11+ y acceso al modelo elegido. Invoca Bedrock y puede generar consumo facturable. El ejemplo elige `amazon.nova-micro-v1:0` en `us-east-1`; comprueba que tu cuenta tenga acceso antes de ejecutarlo. El runner [bedrock_e2e.py](booking_lab/bedrock_e2e.py) crea su propio laboratorio; no requiere mantener abierta la demo de las secciones anteriores.

Desde la raíz del repo:

```bash
python3 booking_lab/bedrock_e2e.py \
  --live-bedrock --confirm-test-operator \
  --model-id amazon.nova-micro-v1:0 --region us-east-1 \
  --output .local/bedrock-live-01.json
```

La ejecución del **18 de octubre de 2026 en CCS** pasó **7/7 casos con cuatro inferencias reales**; el [registro público](evidence/bedrock/README.md) incluye el rechazo incorrecto de consulta del primer intento y la corrección.

Ambas opciones de autorización son necesarias. `--live-bedrock` habilita **hasta cuatro llamadas reales** a Converse: un intento por llamada, sin reintentos automáticos del CLI, con un máximo de 512 tokens de salida solicitado por llamada y sin fallback a `rules`. El adaptador solicita `temperature=0.00001`, el mínimo documentado de Nova, sin prometer determinismo del modelo. Una falla detiene el recorrido y conserva la evidencia; no se repite la inferencia para buscar una respuesta favorable.

`--confirm-test-operator` activa un **aprobador de fixture sintético**. El runner compara la acción del modelo con la acción exacta esperada y solo entonces envía `APROBAR <digest>` a la CLI. Esta confirmación comprueba el contrato de aprobación y su aplicación en la API; no acredita una identidad humana independiente del emisor didáctico. La demo interactiva de la sección 6 conserva la revisión manual de cada propuesta.

| Inferencia | Intención en lenguaje natural | Aceptación requerida |
| --- | --- | --- |
| 1. Importe ausente | Preparar BOG-MDE sin proporcionar importe y sin inventarlo | Respuesta exacta `{"action":"unsupported"}`; rechazo antes de crear plan, reserva o cobro |
| 2. Crear | Proponer BOG-MDE por exactamente 12500 unidades menores sintéticas | Acción `create` con esos dos valores exactos; sin aprobación no hay efectos |
| 3. Consultar | Mostrar las reservas actuales sin modificarlas | Acción `list`; resultado HTTP con la reserva creada y aislamiento por sujeto |
| 4. Cancelar | Proponer cancelar únicamente el ID creado y esperar aprobación | Acción `cancel` con ese ID exacto; aprobación nueva y un solo reembolso |

Si el modelo inventa el importe del caso negativo o propone otra acción, el recorrido falla y no la aprueba. Un JSON rechazado por formato o una indisponibilidad de AWS tampoco se contabilizan como rechazo semántico correcto.

Después de aprobar la creación, la prueba interrumpe el proveedor de pagos y reanuda desde el mismo estado persistido. Comprueba la recuperación **sin una inferencia adicional ni otro cobro**. También compara una restauración PostgreSQL con una instantánea consistente, verifica auditoría firmada y revisa las invariantes finales.

Para aceptar una ejecución, exige `result: passed`, todos los casos aprobados, cuatro respuestas de modelo completas, tres planes positivos exactos, un rechazo semántico esperado, `rules_fallback_used: false`, invariantes finales satisfechas, `cleanup.result: passed`, `cleanup.all_stopped_verified: true`, cero estados desconocidos y `test_containers_running: 0`. El cierre registra los resultados de `stop` e `inspect` por contenedor: una inspección fallida no equivale a estar detenido y hace fallar la ejecución. El JSON registra el commit y hashes del código, los recibos de inferencia y los resultados de DB. Un preflight de acceso o una propuesta del modelo por sí solos no cumplen esa aceptación.

**Cada repetición necesita un archivo nuevo**, por ejemplo `.local/bedrock-live-02.json`; el runner rechaza un destino existente. Conserva también las ejecuciones fallidas. Si deseas etiquetar el entorno, antepone `LAB_EVIDENCE_ENV='AWS CloudShell CCS'` al comando; esa etiqueta describe el entorno declarado y no sustituye la evidencia de ejecución.

## 8. Verifica el recorrido determinista y cierra

```bash
python3 -m unittest discover -s tests -v
python3 booking_lab/run.py e2e --output .local/agent-db-e2e.json
```

El E2E determinista incluye la CLI real, denegaciones de aprobación en la API, rechazo sin efectos, creación/consulta/cancelación, integridad del plan, aislamiento de sujeto, caída del proveedor y caída de API después de cobrar. Los casos existentes siguen comprobando concurrencia, compensación, auditoría y restauración de PostgreSQL/SQLite. El recibo registra casos, invariantes, hashes y modo del planificador. Este comando y la CI habitual no activan el runner de Bedrock real.

Termina la demo con Ctrl+C en su primera terminal. El runner detiene solo sus contenedores y conserva los archivos privados para revisión. Relaciona el resultado con tu [ficha de valor](FICHA_VALOR.md) y registra la decisión en los [artefactos de AI-DLC](AI_DLC.md).
