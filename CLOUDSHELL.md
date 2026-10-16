# Preparar una cuenta propia con CloudShell

**Ruta completa MIT:** para reservas, PostgreSQL, auditoría y recuperación utiliza [LABORATORIO_MIT.md](LABORATORIO_MIT.md). Solo requiere clonar este repo y ejecutar `python3 booking_lab/run.py e2e --output .local/db-e2e.json`; los pasos históricos de ATX continúan abajo.

Recorrido observado el 16 de octubre de 2026 (UTC): CloudShell Linux x86_64 en `us-east-1`, Node **22.23.3**, ATX **3.19.0**, Python **3.13.15**. La instalación y A–C pasaron en una cuenta distinta de la del evento. La evidencia de D–I se informa por separado en [CCS_E2E.md](CCS_E2E.md).

## 1. Cuenta y herramientas

Abre CloudShell desde la sesión de la cuenta donde tienes autorización para ejecutar el taller. Comprueba en privado `aws sts get-caller-identity`. No copies credenciales del evento. Se necesitan los [permisos oficiales de Transform](https://docs.aws.amazon.com/transform/latest/userguide/ct-getting-started.html); `atx ct status --health` comprueba disponibilidad, pero no certifica todos los permisos de una ejecución.

El CloudShell observado tenía Node 20. La siguiente preparación instala una versión compatible dentro de un directorio nuevo. Los números están fijados para reproducir esta prueba; revisa actualizaciones de seguridad antes de reutilizarlos en el futuro.

```bash
set -euo pipefail
# Bash; elige un directorio que aún no exista.
export LAB_ROOT="$HOME/workshop-replay-20261016"
mkdir "$LAB_ROOT"
cd "$LAB_ROOT"
test "$(uname -m)" = x86_64
curl -fsSLO https://nodejs.org/dist/v22.23.3/node-v22.23.3-linux-x64.tar.xz
curl -fsSLO https://nodejs.org/dist/v22.23.3/SHASUMS256.txt
grep ' node-v22.23.3-linux-x64.tar.xz$' SHASUMS256.txt | sha256sum --check
tar -xf node-v22.23.3-linux-x64.tar.xz
export PATH="$LAB_ROOT/node-v22.23.3-linux-x64/bin:$HOME/.local/bin:$PATH"
curl -fsSL https://transform-cli.awsstatic.com/install.sh -o install-atx.sh
# Revisa el instalador oficial antes de ejecutarlo.
bash install-atx.sh 3.19.0
node --version
atx --version
atx ct status --health
atx custom def list
```

Los bloques usan `set -euo pipefail`: si una comprobación falla, se detienen; abre otra terminal y corrige la causa antes de repetirlos. La prueba partió de un CloudShell sin ATX instalado. En un entorno existente revisa primero `command -v atx` y `atx --version`: el instalador actualiza el enlace de `~/.local/bin/atx`. Para retomar en otra terminal vuelve a exportar `LAB_ROOT`, `PATH` y `AWS_REGION=us-east-1`.

## 2. Restauración y prueba verificable

Usa **Actions → Upload file** para cargar la captura autorizada; CloudShell la guarda en tu directorio personal. El archivo no viene en el repositorio público. Ejecuta:

```bash
set -euo pipefail
cd "$LAB_ROOT"
git clone https://github.com/sjaramillov/agentic-transformation-workshop-latam.git replica
git -C replica rev-parse HEAD
python3 replica/scripts/lab.py restore \
  --archive "$HOME/agentic-workshop-materials-2026-10-15.tar.gz" \
  --destination environment
python3 replica/scripts/lab.py rehearse --environment environment --output practica
WORKSHOP_ARCHIVE="$HOME/agentic-workshop-materials-2026-10-15.tar.gz" \
  python3 -m unittest discover -s replica/tests -v
```

La prueba realizada con el commit `fb681911bfc7b1ccb181d9df9a38a3bcfb3e4945` produjo **15 pruebas aprobadas, cero omitidas**. `practica/` contiene ocho salidas nuevas, el manifiesto y los contextos ARA/MODA. Conserva el SHA del clon que realmente uses.

## 3. Alcance inicial de un solo servicio

Para medir desde el código inicial, prepara una copia adicional de booking-service. Este bloque modifica únicamente el clon nuevo `source/booking-service`; exige que ese destino no exista. Conserva intacta la restauración `environment/`.

```bash
set -euo pipefail
export PORTFOLIO="$LAB_ROOT/environment/apps/travelcorp-portfolio"
export AWS_REGION=us-east-1
export LAB_SOURCE=workshop-replay-20261016

git clone --no-hardlinks --single-branch --branch main \
  "$PORTFOLIO/src/booking-service" "$LAB_ROOT/source/booking-service"
git -C "$LAB_ROOT/source/booking-service" switch -C main \
  2ef490d9a411a5f0edd1b497553dcb3def5dd580
git -C "$LAB_ROOT/source/booking-service" remote remove origin
git -C "$LAB_ROOT/source/booking-service" config user.name 'Workshop E2E'
git -C "$LAB_ROOT/source/booking-service" config user.email 'workshop-e2e@example.invalid'
git -C "$LAB_ROOT/source/booking-service" status --short --branch
atx ct source list
# Usa LAB_SOURCE solo si ese nombre todavía no existe.
atx ct source add --name "$LAB_SOURCE" --provider local --path "$LAB_ROOT/source"
atx ct discovery scan --source "$LAB_SOURCE"
atx ct repository list --source "$LAB_SOURCE"
```

Éxito: un único slug `$LAB_SOURCE::booking-service`. Los contextos proceden de la práctica nueva, por ejemplo `ARA_CONTEXT="$(cat "$LAB_ROOT/practica/context-ara.txt")"`. Usa ese slug, el contexto y `--agent-scope write-enabled` en el recorrido de [EJECUCION_AWS.md](EJECUCION_AWS.md). Para la remediación usa el YAML de **`practica/atx-config-ara.yaml`**, no un archivo histórico por accidente.

## 4. Seguimiento y consumo

Las ejecuciones de Transform tienen [precio por minuto de agente](https://aws.amazon.com/transform/pricing/); el consumo no equivale al tiempo de reloj. En ATX 3.19.0, `atx custom def exec --help` expone `--limit <minutes>`. **No se ha verificado que `atx ct analysis run` propague esa opción a su ejecución hija**: no la presentes como un límite confirmado para CT.

En otra pestaña de CloudShell, con el mismo PATH, consulta el ID exacto:

```bash
atx ct analysis get --id ID --json
# Solo para detener tu propia ejecución identificada:
atx ct analysis cancel --id ID
```

No confundas `running` con éxito. Espera el estado final y los informes asociados. Guarda logs e inventarios antes de que termine la sesión; descarga solo los archivos de evidencia necesarios, sin credenciales. Conserva los identificadores de cuenta y los registros crudos en almacenamiento privado.

Antes de aceptar una remediación, revisa [LIMITACIONES_TD.md](LIMITACIONES_TD.md). CloudShell permite ejecutar el análisis sobre archivos; no acredita que la aplicación propuesta esté desplegada ni disponible.

Para probar imágenes, revisa primero el espacio de Docker y [las comprobaciones de runtime](RUNTIME_LOCAL.md). La ejecución observada agotó el disco durante un build adicional; CloudShell resultó más directo para ATX que para mantener varias imágenes de aplicación y bases de datos.
