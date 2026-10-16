> **Archivo histórico del 16 de octubre de 2026.** Describe otra implementación. El workshop público vigente comienza en [Inicio rápido](../INICIO_RAPIDO.md).

# Guía para replicar el Agentic Transformation Workshop

> **Ruta recomendada:** empieza por [INICIO_RAPIDO.md](INICIO_RAPIDO.md). Esta guía explica A–J; [EJECUCION_AWS.md](EJECUCION_AWS.md) reúne la preparación operativa y los criterios de aceptación.

## 1. Alcance del taller

El taller sigue una cadena completa sobre TravelCorp, una compañía ficticia de viajes. A–C modelan el proceso y diseñan un agente; D–E miden las aplicaciones con Agentic Readiness Analysis (ARA) y Modernization Readiness Analysis (MODA); F escala las mediciones a todos los repositorios; G organiza el trabajo; H aplica dos cambios acotados mediante Transformation Definitions (TD); I vuelve a medirlos; J describe cómo operar ese ciclo en una organización.

El caso principal es `booking-service`, un monolito PHP heredado. El diseño de ejemplo es un agente de rebooking con autonomía P (prepara una propuesta que una persona aprueba). Sus hallazgos ilustran dos ejes independientes: modernizar la plataforma y permitir que un agente opere con seguridad.

**Implementación para repetirlo:** [booking_lab/](../booking_lab/) contiene un servicio original MIT con el mismo problema didáctico de reservas, pagos y preparación para agentes. El [laboratorio completo](../LABORATORIO_MIT.md) usa únicamente este clon público. Las rutas TravelCorp que siguen describen el entorno histórico del evento y permiten contrastar sus resultados; son una ruta adicional.

## 2. Requisitos y preparación

### Cuenta y entorno

Para ejecutar D–I se necesita una cuenta AWS con los permisos específicos documentados por AWS Transform. No hace falta una cuenta AWS para A–C offline. La política `static/iam_policy.json` mencionada por el evento no está incluida en esta copia; no asumir que se necesita administración para todos los pasos. Se recomienda usar una cuenta no productiva y una región donde estén disponibles AWS Transform y los servicios usados. El evento usaba `us-east-1`; sus cuentas temporales se reciclaban al terminar.

El entorno original usaba un IDE VS Code Server en EC2 detrás de CloudFront. El stack `VsCodeServerIDE` creaba VPC, subred, gateway, `t3.large`, rol de instancia, parámetro SSM y distribución CloudFront. En una réplica propia, revisar primero la arquitectura, permisos, costos y estado actual de AWS Transform. La página del taller daba una estimación orientativa de USD 3–5 para una sesión de 3 horas, principalmente por Bedrock y la instancia; no usar esa cifra como cotización actual.

**Límite de esta copia:** las páginas capturadas corresponden a la modalidad atendida por el evento y presuponen que Workshop Studio ya aprovisionó el IDE y los recursos AWS. El archivo local conserva el código de TravelCorp, el orquestador del IDE y los informes disponibles, pero no la plantilla de aprovisionamiento del evento, la cuenta temporal, las credenciales ni los recursos en ejecución. Para repetirlo en una cuenta propia, primero hay que conseguir la guía o plantilla vigente de modalidad self-paced, o reconstruir y validar esa infraestructura por separado; el recorrido de ejercicios de este documento no basta para crearla desde cero.

### Herramientas y archivos

El IDE del evento ya tenía el CLI `atx`, Kiro CLI, AWS CLI, Python 3.11, Docker, el paquete Python `strands`, el material TravelCorp y el orquestador. Para la práctica offline bastan Python 3.11+ y Bash. Para la ejecución AWS se necesitan además Git, Node.js 22+, jq, ATX, AWS CLI y Kiro; Strands/boto3 solo para las conversaciones de A–C en vivo. Docker corresponde al trabajo con contenedores, no a leer informes. Confirma las herramientas de la ruta elegida:

```bash
git --version
node --version
jq --version
atx --version
kiro-cli --version
aws --version
python3 --version
docker --version
python3 -c "import strands; print('Strands OK')"
```

El árbol base está en `~/environment/apps/travelcorp-portfolio/`:

```text
src/                    los tres repositorios de servicios
exercises/              facilitador AgentStorming y scripts de informes
custom-td/              definición para desbloquear booking-service
custom-td-containerize/ definición para contenerizar servicios PHP/Apache
platform-team/          pipeline y plantillas de infraestructura
precomputed-reports/    informes de respaldo
portfolio-config.yaml   configuración usada por el orquestador
```

Solo `src/` se registra como fuente de análisis; así los directorios de soporte no se confunden con repositorios de aplicaciones. El archivo comprimido de `resources/` conserva la copia descargada del IDE, el orquestador de esa sesión y los informes actuales.

### Acceso a AWS Transform y Kiro

1. En la cuenta del evento, selecciona `us-east-1` y habilita la aplicación web de AWS Transform con **Quick start**. La guía advertía que algunas decisiones de **Manual setup** no se pueden cambiar después de habilitar el servicio.
2. Abre la URL de la aplicación web que aparece en Service management y entra en **Continuous modernization**. El dashboard puede decir que no hay análisis hasta que corra el primero; la lista CLI confirma la fuente.
3. El IDE del evento ya tenía `atx` configurado. En un equipo nuevo, instala el CLI según la guía oficial y comprueba su ayuda; evita reemplazar a ciegas la versión preinstalada del evento.
4. Para Kiro CLI usa el flujo de dispositivo con un AWS Builder ID:

```bash
kiro-cli login --use-device-flow
kiro-cli chat
```

Confirma el código de dispositivo en el navegador cuando tú ejecutes el taller. Las conversaciones se guardan desde Kiro con `/chat save nombre.json`; ese comando se escribe dentro de la conversación, no en la shell.

### Registrar el origen

Comprueba la fuente y los tres servicios esperados:

```bash
atx ct repository list --source travelcorp
```

Si la fuente no existe, el taller proponía registrar el directorio padre de los repositorios y descubrirlos:

```bash
atx ct source add --name travelcorp --provider local \
  --path "$HOME/environment/apps/travelcorp-portfolio/src"
atx ct discovery scan --source travelcorp
atx ct repository list --source travelcorp
```

Los slugs esperados son `travelcorp::booking-service`, `travelcorp::notification-service` y `travelcorp::payment-gateway`. Cada subdirectorio debe ser un repositorio Git con la rama `main` disponible. En el evento, el arranque del IDE había ejecutado `atx ct remote provision --mode batch` y la infraestructura remota ya estaba preparada. Aun así, los análisis de A–I corren *in-process* en el IDE: esa infraestructura remota no es requisito para el recorrido.

#### Infraestructura remota opcional

Una cuenta nueva puede mostrar en AWS Transform una página para desplegar dispatcher, scheduler y cómputo de análisis/remediación en AWS Batch. Ese modo remoto sirve para ejecutar análisis a escala y con programación; no se necesita para las corridas manuales del taller. La configuración de Batch exige subredes privadas con salida mediante NAT o VPC endpoints y DNS habilitado en la VPC. `atx ct remote network discover` informa si una red existente cumple; `atx ct remote network create` crea una VPC y sí aprovisiona recursos. Antes de desplegarlo en una cuenta propia, confirma permisos, arquitectura y costos con las instrucciones vigentes de AWS Transform.

### Ruta para los comandos siguientes

En cada terminal Bash define la raíz de tu entorno (el IDE usa `~/environment`; la práctica local usa el destino de restauración):

```bash
export LAB_ENV="${LAB_ENV:-$HOME/environment}"
```

## 3. Módulos A–C: modelar y diseñar

Las tres primeras fases usan un facilitador de sala simulado. Agrega `--offline` a cada comando para usar diálogos predeterminados sin Bedrock. La ruta automatizada y aislada está en el inicio rápido. Cada fase genera su propio archivo de tablero Markdown, JSON de transferencia y decisiones en `run-manifest.json`. Mantén la terminal del facilitador abierta; abre una segunda terminal para editar o previsualizar el tablero.

### A. Modelar el proceso

```bash
cd "$LAB_ENV/apps/travelcorp-portfolio/exercises"
python3 -m agentstorming.facilitate
```

La sala representa a responsables de atención, producto, operaciones, alianzas y arquitectura. El objetivo es mapear eventos, comandos, políticas, actores, lecturas de datos, sistemas externos y puntos de dolor. Los artefactos son `eventstorm-output.md` y `eventstorm-board.json`.

La historia de ejemplo sigue búsqueda, reserva, cancelación de aerolínea, evaluación de reembolso, rebooking, reembolso, excepción de socio y cierre del itinerario. Hay una frontera entre el flujo regular y las excepciones. El historial de excepciones distribuido en correos y documentos no es accesible por API, lo que condiciona la decisión del módulo B.

### B. Decidir dónde aporta un agente

```bash
python3 -m agentstorming.facilitate --phase 2
```

Clasifica decisiones por intensidad de juicio y disponibilidad de datos; agrupa políticas en áreas de decisión, las ubica en una matriz y asigna un nivel de autonomía:

| Código | Nivel | Supervisión |
| --- | --- | --- |
| A | Assisted | La persona realiza cada acción. |
| P | Prepares | El agente propone; una persona aprueba antes de ejecutar. |
| E | Executes | El agente actúa dentro de límites y una persona revisa después. |
| G | Governs | El agente ajusta límites bajo políticas y revisión periódica. |

Las decisiones con mucho juicio y datos disponibles son candidatas a agente; las que carecen de acceso a datos necesitan primero trabajo de integración. El ejemplo coloca rebooking y elegibilidad de reembolso como candidatas, ambas inicialmente en P. Reembolsos conservan un marcador de aprobación humana por mover dinero. Los resultados son `quadrant-output.md` y `quadrant-board.json`.

### C. Diseñar el workflow

```bash
python3 -m agentstorming.facilitate --phase 3
```

Construye cuatro carriles: sistemas externos, datos, agente y persona. En el ejemplo, un evento inicia el proceso; el agente reúne opciones y redacta una recomendación; Step Functions espera la decisión de la persona; tras la aprobación se registra y notifica; CloudWatch mide duración y frecuencia de anulaciones. Marca cada endpoint como **Tool** si produce efectos o **Resource** si solo consulta datos.

El tablero `workflow-design-output.md` queda en `exercises/`; `atx-config-ara.yaml`, `atx-config-mod.yaml` y `run-manifest.json` se escriben en el directorio padre `travelcorp-portfolio/`. El módulo D y el módulo H usan el contexto ARA; los módulos E y G usan la intención de modernización. Cierra las previsualizaciones anteriores antes de cada fase para no confundir tableros.

## 4. Módulos D–G: medir, relacionar y priorizar

### D. ARA para `booking-service`

ARA evalúa si un agente puede operar de manera segura sobre el servicio. Sus ocho dimensiones cubren API, autenticación, estado, supervisión humana, datos, descubrimiento/documentación, observabilidad y madurez de ingeniería. Las categorías del informe son `BLOCKER`, `RISK-SAFETY`, `RISK-QUALITY` e `INFO`.

```bash
atx ct analysis run \
  --type agentic-readiness \
  --repo travelcorp::booking-service \
  --source travelcorp \
  --agent-scope write-enabled \
  --context "$(bash "$LAB_ENV/apps/travelcorp-portfolio/exercises/build-atx-context.sh" ara)"
```

`--agent-scope write-enabled` evalúa el servicio como una API que puede registrar o modificar reservas. El contexto del ejercicio A–C personaliza la evaluación a los endpoints del agente; si se saltan esas fases, el escaneo puede correrse sin ese contexto. ARA es una evaluación: no incluye una transformación que arregle automáticamente sus hallazgos.

ARA puede tardar 15–25 minutos. Consulta el estado desde otra terminal:

```bash
atx ct analysis list --type agentic-readiness --json
# Usa el ID de tu ejecución; el primer elemento puede ser de otra corrida.
atx ct analysis get --id ID --json
```

El CLI hace un resumen de portafolio después del análisis de un repositorio. Verifica por separado el estado del ID de análisis y sus artefactos; no ignores errores genéricamente porque parezcan del rollup. Si sigue `running` por más de 25 minutos sin avance, inspecciona el ID antes de cancelar y reintentar; una ejecución zombi puede bloquear una relectura posterior.

Conserva primero una copia en un directorio nuevo con `lab.py collect` (inicio rápido). El siguiente es el comando original, reservado al IDE: puede eliminar reportes previos y terminar el proceso del puerto 9090 antes de iniciar un servidor. Lee su código antes de reutilizarlo en otra máquina.

Consolidación original del evento:

```bash
bash "$LAB_ENV/apps/travelcorp-portfolio/exercises/consolidate-reports.sh" \
  --repo booking-service
```

La salida se guarda en `~/environment/reports/ara/` como Markdown, JSON, HTML y metadatos. Para la clasificación automatizada, inspecciona el JSON (`.classification`); para evidencia, ruta de código y razonamiento, usa el Markdown/HTML. El baseline precomputado tiene seis bloqueadores; la captura de ARA tiene cinco. No son el mismo resultado. El ejemplo estático enumera: autenticación de máquina, auditoría, contrato API, idempotencia, clasificación de datos y compensación transaccional.

### E. MODA para `booking-service`

Ejecuta MODA después de finalizar ARA para no correr dos análisis sobre el mismo origen al mismo tiempo:

```bash
atx ct analysis run \
  --type modernization-readiness \
  --repo travelcorp::booking-service \
  --source travelcorp \
  --context "$(bash "$LAB_ENV/apps/travelcorp-portfolio/exercises/build-atx-context.sh" mod)" \
  --prefer eks \
  --avoid self-managed-mysql,manual-deployments,monolith-in-place
```

MODA revisa INF, APP, DATA, SEC y OPS, puntúa preparación y señala pathways de modernización. `--prefer` y `--avoid` orientan las rutas recomendadas, no cambian si una ruta se activa. El ejemplo destaca `INF-Q1` (cómputo EC2 sin contenedor) y activa **Move to Containers**. Usa el mismo sondeo de estado cambiando el tipo a `modernization-readiness`, y luego el script de consolidación.

Con Kiro, relaciona cada bloqueo ARA con una ruta MODA que lo resolvería y separa los hallazgos que afectan los endpoints del agente de los que pueden quedar diferidos. Guarda los resultados como `blocker-route-map.md` y `touchpoint-prioritized-findings.md`; guarda la sesión con `/chat save moda-session.json`.

No compares el conteo total del dashboard con el del informe como medida de éxito: ambas superficies pueden agrupar hallazgos de manera distinta. Usa clasificación, bloqueadores y pathways.

### F. Escalar al portafolio (opcional)

Al omitir `--repo`, el CLI examina todos los repositorios descubiertos y agrega sus resultados. El módulo trae informes precomputados para revisar antes de invertir 15–30 minutos en una corrida en vivo:

```bash
atx ct analysis run --type agentic-readiness --source travelcorp \
  --agent-scope write-enabled \
  --context "$(bash "$LAB_ENV/apps/travelcorp-portfolio/exercises/build-atx-context.sh" ara)"

atx ct analysis run --type modernization-readiness --source travelcorp \
  --context "$(bash "$LAB_ENV/apps/travelcorp-portfolio/exercises/build-atx-context.sh" mod)" \
  --prefer eks \
  --avoid self-managed-mysql,manual-deployments,monolith-in-place
```

En el ejemplo, `payment-gateway` sirve como referencia más moderna; `booking-service` y `notification-service` conservan bloqueadores. El informe agregado puede incluir patrones transversales y no reemplaza la clasificación por repositorio. Si solo haces una corrida, MODA es la que permite comprobar a nivel portafolio el efecto de contenerizar `booking-service`.

### G. Construir la hoja de ruta

Kiro lee las salidas A–C, ambos informes y los dos archivos de mapeo. Pídele enumerar todos los bloqueadores ARA y pathways MODA activados, asociarlos con agentes y servicios, y agruparlos en cuatro fases: victorias rápidas, despejar el camino del agente prioritario, resto de remediaciones y desbloqueos de datos con posible equipo dueño.

Puedes usar las plantillas de [PROMPTS.md](../PROMPTS.md). Guarda el resultado como `prioritized-roadmap.md`. Revisa con criterio humano el orden, la capacidad de los equipos y los puntos donde las tareas compiten por las mismas personas. El ejemplo pone primero `booking-service`, porque el agente de rebooking depende de él y necesita resolver `INF-Q1` y `AUTH-Q1`.

## 5. Módulos H–I: cambiar y comprobar

### H. Aplicar remediaciones locales

El taller publica dos TD personalizados:

- `workshop-containerize-to-eks`: genera Dockerfile, manifiestos Kubernetes y externaliza configuración para preparar PHP/Apache para EKS.
- `workshop-booking-service-fix-blockers`: añade identidad de máquina y controles de API, auditoría, datos y consistencia para la ruta del agente.

Los comandos completos de publicación, compatibles con la ayuda disponible, están en [EJECUCION_AWS.md](EJECUCION_AWS.md). Antes de `remediation create`, inspecciona `git status`, conserva cualquier informe y confirma que no haya cambios sin revisar. La guía original propone limpiar artefactos de informes dentro del repositorio, pero esa limpieza borra la carpeta `services/`; no ejecutes comandos `rm -rf` sin inspeccionar la ruta y guardar lo que necesites.

Contenerización:

```bash
atx ct remediation create \
  --repo travelcorp::booking-service \
  --source travelcorp \
  --transformation-name workshop-containerize-to-eks \
  --name containerize \
  --local
```

Consulta `atx ct remediation status --id ID --json` y revisa el diff de la rama exacta devuelta por esa remediación. No elijas la rama más reciente: los análisis también pueden dejar ramas temporales. `--local` crea cambios locales y no un PR ni recursos AWS. Los archivos Docker/Kubernetes por sí solos no limpian `INF-Q1`: la plantilla de infraestructura debe dejar de apuntar a EC2 y el pipeline debe desplegar en el clúster compartido `cluster-x`. Los archivos `platform-team/` del paquete describen ese pipeline y la plantilla posterior. Revisa el diff y decide manualmente si se integra a `main`.

Para la ruta de desbloqueo de ARA, requiere `atx-config-ara.yaml` de C:

```bash
atx ct remediation create \
  --repo travelcorp::booking-service \
  --source travelcorp \
  --transformation-name workshop-booking-service-fix-blockers \
  --name fix-auth-blockers \
  -g "file://$LAB_ENV/apps/travelcorp-portfolio/atx-config-ara.yaml" \
  --local
```

El `-g` es importante: dirige los cambios al diseño, endpoints y autonomía del agente seleccionado. Revisa a mano la rama y confirma que los cambios propuestos coincidan con la política y la arquitectura antes de integrarlos. El ejemplo agrega API Gateway/Cognito M2M/JWT, auditoría, claves de idempotencia, filtrado de PII, metadatos de residencia y compensación de reservas fallidas.

### I. Volver a medir

Guarda informes “antes” y confirma que los cambios aprobados están en `main`; la herramienta analiza la rama predeterminada. Vuelve a ejecutar discovery scan y el mismo tipo de análisis con el mismo alcance. Para evitar resultados de HTML desactualizados, conserva los snapshots y revisa Markdown/JSON como referencia si el HTML parece igual al anterior.

Consolidación selectiva:

```bash
bash "$LAB_ENV/apps/travelcorp-portfolio/exercises/consolidate-reports.sh" \
  --repo booking-service --only moda

bash "$LAB_ENV/apps/travelcorp-portfolio/exercises/consolidate-reports.sh" \
  --repo booking-service --only ara
```

El resultado esperado por el ejercicio es que MODA deje de activar **Move to Containers** cuando `INF-Q1` se resuelve, aunque su tier permanece `Remediation Required` por otros hallazgos. El ejercicio espera que ARA llegue a `Pilot-Ready` al resolver los bloqueadores write-enabled; una salida generativa no garantiza ese resultado y debe comprobarse. Compara findings concretos y pathways, no solo totales: la remediación es una hipótesis hasta que el nuevo análisis la confirma.

## 6. Módulo J: operar el ciclo en una organización

AWS Transform proporciona el motor de análisis, el catálogo y el flujo de remediación. La organización provee el contenido de los TD y la plataforma destino donde el cambio funcionará. Antes de ejecutar una TD, verifica que existen y están operados el clúster, la canalización, los módulos de infraestructura y la identidad que requiere el cambio.

Roles que el taller sugiere nombrar: responsables de arquitectura/servicio para priorizar; plataforma para operar el destino y curar el catálogo TD; aplicaciones para revisar e integrar los diffs; seguridad/compliance para fijar la política; SRE para atender el servicio modificado; identidad para el proveedor de tokens; y patrocinio de ingeniería para financiar la revisión de PRs.

Los TD no son deterministas como módulos Terraform: su salida depende del prompt, versión de modelo y estado del repositorio. Antes de expandirlos, conserva versiones de herramienta/modelo, pruébalos contra repositorios representativos, exige guardas de entrada y reentrada, declara supuestos de runtime y conflictos con otras TD, y despliega primero a un servicio canario. El módulo enfatiza revisión conjunta entre quien mantiene la TD y quien posee el servicio, puertas automáticas de política, pruebas del servicio, capacidad de revisión, rollback y responsable de incidentes.

Si IaC y aplicación viven en repos distintos, una remediación puede requerir dos TDs y una secuencia segura. Antes de escribir una TD, comprueba si el arreglo corresponde a un módulo compartido o a un cambio mecánico que conviene resolver con un codemod reproducible.

Para operar continuamente, define cadencia de escaneos, responsable de fallos y métricas de proceso: tiempo de remediación por severidad, porcentaje de estate en la golden path, cobertura TD de hallazgos abiertos, y hallazgos corregidos que luego reaparecen.

## 7. Cierre y límites de esta copia

El evento AWS terminaba automáticamente; en una cuenta propia el stack `VsCodeServerIDE` mantiene recursos facturables. Antes de retirarlo, conserva `custom-td/`, `custom-td-containerize/` e informes. La página del taller daba como limpieza de referencia:

```bash
aws cloudformation delete-stack --stack-name VsCodeServerIDE
aws cloudformation wait stack-delete-complete --stack-name VsCodeServerIDE
```

Este comando elimina esa pila y el IDE, pero puede dejar otras pilas creadas para ATX remoto o despliegues. Inventaría los recursos antes y después; no asumas que terminaron todos los cargos. Ejecutarlo solo en tu propia cuenta, después de verificar el nombre de pila y respaldar todo lo que quieras conservar. No se ejecutó como parte de esta captura.

La copia local conserva una guía de trabajo, enlaces de referencia, el paquete TravelCorp del IDE y el repositorio público del orquestador. No conserva el sandbox AWS activo ni sus credenciales. Antes de una réplica real, confirma disponibilidad regional, modelo de Bedrock, versión CLI, permisos IAM, costos y cualquier cambio reciente en la documentación oficial.
