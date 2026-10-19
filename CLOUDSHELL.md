# Ejecutar el workshop en AWS CloudShell

Para empezar por las preguntas, cliente y tableros, completa primero la [guía paso a paso](GUIA_REPLICACION.md) en tu equipo. El coach abre un servidor local en ese equipo. Esta página cubre la ejecución técnica en CloudShell.

Abre CloudShell en la cuenta y región que usarás. El ejemplo utiliza `us-east-1`. Comprueba en privado tu identidad con `aws sts get-caller-identity`.

| Recorrido | Requisitos |
| --- | --- |
| Laboratorio y agente determinista | Python 3.11+, Git y Docker operativo |
| Agente con Bedrock | Los anteriores, AWS CLI y `bedrock:InvokeModel` sobre el modelo elegido |
| ARA/MODA con AWS Transform | ATX y [permisos de AWS Transform](https://docs.aws.amazon.com/transform/latest/userguide/ct-getting-started.html) |

Bedrock y Transform consumen servicios AWS. Los pagos de la aplicación son sintéticos. Mantén en privado las credenciales, sesiones, archivos `.env` y logs de depuración.

## 1. Comprueba herramientas y clona

```bash
python3 --version
git --version
docker info
aws --version
git clone https://github.com/sjaramillov/agentic-transformation-workshop-latam.git
cd agentic-transformation-workshop-latam
export WORKSHOP_ROOT="$PWD"
```

Si `docker info` falla, resuelve el acceso al daemon antes de continuar. Ejecuta los siguientes pasos desde `$WORKSHOP_ROOT`.

## 2. Valida la aplicación y prepara los ejercicios

```bash
LAB_EVIDENCE_ENV='AWS CloudShell' \
python3 booking_lab/run.py e2e --output .local/db-e2e.json
```

**Resultado esperado:** pruebas aprobadas y `.local/db-e2e.json` con `result: passed` y `test_containers_running: 0`. Este recorrido funciona sin ATX ni inferencias Bedrock.

Para crear, consultar y cancelar reservas con aprobación interactiva, sigue [Agente ejecutable](AGENTE_EJECUTABLE.md).

## 3. Valida el agente con Bedrock real

Comprueba que tu cuenta tenga acceso a `amazon.nova-micro-v1:0` en `us-east-1`, o sustituye modelo y región por los que usarás. El comando crea su propio laboratorio PostgreSQL y realiza hasta cuatro inferencias facturables:

```bash
LAB_EVIDENCE_ENV='AWS CloudShell' \
python3 booking_lab/bedrock_e2e.py \
  --live-bedrock --confirm-test-operator \
  --model-id amazon.nova-micro-v1:0 --region us-east-1 \
  --output .local/bedrock-live-01.json
```

`--confirm-test-operator` autoriza al runner a aprobar las propuestas que coincidan exactamente con los casos de prueba. Para revisar y aprobar manualmente cada propuesta, usa la [demo Bedrock](AGENTE_EJECUTABLE.md#5-usa-bedrock-para-interpretar-el-objetivo).

**Resultado esperado:** siete casos aprobados, `result: passed`, `cleanup.result: passed` y `test_containers_running: 0`. El flujo comprueba creación, consulta, cancelación, recuperación, auditoría y restauración. Usa **un output nuevo por corrida**, por ejemplo `.local/bedrock-live-02.json`; los archivos existentes se conservan.

Si falla el acceso al modelo, revisa cuenta, región y permiso `bedrock:InvokeModel`. Si una propuesta es rechazada, consulta el mensaje y corrige el objetivo o la configuración; no se sustituye Bedrock por otro planificador. Los [recibos y criterios detallados](evidence/bedrock/README.md) están disponibles como referencia.

## 4. Prepara ATX para ARA/MODA

Al continuar en Ejecución AWS elegirás la sesión de discovery y prepararás sus fuentes. Para conservar el trabajo hecho en tu equipo, sube su `session.json` a `.local/discovery-01/` del clon y usa la misma revisión de Git. Puedes comprobarla con `git rev-parse HEAD` en ambos equipos.

Si `atx --version` y `atx ct status --health` funcionan, continúa en [Ejecución AWS](EJECUCION_AWS.md). Si falta ATX, este ejemplo instala Node 22.23.3 y ATX 3.19.0 en Linux x86_64. Consulta también la [instalación oficial](https://docs.aws.amazon.com/transform/latest/userguide/custom.html).

```bash
set -euo pipefail
export ATX_TOOLS="$HOME/mit-workshop-tools"
mkdir -p "$ATX_TOOLS"
cd "$ATX_TOOLS"
test "$(uname -m)" = x86_64
curl -fsSLO https://nodejs.org/dist/v22.23.3/node-v22.23.3-linux-x64.tar.xz
curl -fsSLO https://nodejs.org/dist/v22.23.3/SHASUMS256.txt
grep ' node-v22.23.3-linux-x64.tar.xz$' SHASUMS256.txt | sha256sum --check
tar -xf node-v22.23.3-linux-x64.tar.xz
export PATH="$ATX_TOOLS/node-v22.23.3-linux-x64/bin:$HOME/.local/bin:$PATH"
curl -fsSL https://transform-cli.awsstatic.com/install.sh -o install-atx.sh
# Lee install-atx.sh antes de ejecutarlo.
bash install-atx.sh 3.19.0
atx --version
atx ct status --health
cd "$WORKSHOP_ROOT"
```

En cada terminal nueva vuelve a definir `ATX_TOOLS` y el PATH. Con el CLI listo, sigue [Ejecución AWS](EJECUCION_AWS.md) para ejecutar ARA/MODA y revisar sus resultados. Consulta el [precio de los minutos de agente de Transform](https://aws.amazon.com/transform/pricing/).

## 5. Guarda resultados y libera espacio

Usa **Actions → Download file** para descargar los informes seleccionados y el JSON final. Revisa los archivos antes de compartirlos; conserva las sesiones y logs crudos en privado. Descarga también los backups que necesites antes de que se recicle el entorno.

Los runners detienen sus contenedores y conservan datos para revisión. Antes de otra corrida, comprueba `df -h /` y `docker system df`. Para liberar solo los contenedores detenidos de una práctica, utiliza la ruta `review.json` que imprimió su runner:

```bash
python3 scripts/cleanup_lab.py --review .local/db-lab-ID/review.json
python3 scripts/cleanup_lab.py --review .local/db-lab-ID/review.json --remove-stopped
```

El primer comando muestra el alcance; el segundo elimina esos contenedores, conserva logs y volúmenes y rechaza contenedores activos. Si analizaste un clon separado, usa el `review.json` de su propia `.local/`.

| Problema | Acción |
| --- | --- |
| Build o extracción sin espacio | Guarda resultados, elimina los contenedores detenidos de prácticas terminadas y comprueba `df -h /`. |
| El agente devuelve `pending` | Recupera el servicio y repite `execute` con el **mismo estado**; consulta [recuperación](AGENTE_EJECUTABLE.md#4-reanuda-si-hay-un-problema). |
| El cierre no queda en `passed` | Revisa `cleanup` en el JSON y verifica los contenedores indicados antes de eliminarlos o repetir. |
| ATX no aparece en una terminal nueva | Vuelve a exportar `ATX_TOOLS` y el PATH del paso 4. |

Para revisar resultados y controles en detalle, consulta [Auditoría E2E](AUDITORIA_E2E.md). CloudShell mantiene almacenamiento persistente en [`$HOME`](https://docs.aws.amazon.com/cloudshell/latest/userguide/limits.html); conserva aparte los backups del volumen Docker que quieras reutilizar.
