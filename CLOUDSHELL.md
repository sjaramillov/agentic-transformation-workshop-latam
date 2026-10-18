# Ejecutar el workshop público en CloudShell

La réplica se ejecuta en la cuenta que elijas, con el mismo código del repositorio. CCS es el nombre del entorno donde se conservó la evidencia de esta guía.

## 1. Abre tu sesión y verifica herramientas

Abre CloudShell en `us-east-1`. Comprueba en privado la identidad con `aws sts get-caller-identity`. Se requieren los [permisos oficiales de AWS Transform](https://docs.aws.amazon.com/transform/latest/userguide/ct-getting-started.html) para D–I. A–C y el E2E de DB no llaman a Transform.

```bash
python3 --version
git --version
docker info
command -v atx || true
```

## 2. Clona y ejecuta

```bash
git clone https://github.com/sjaramillov/agentic-transformation-workshop-latam.git
cd agentic-transformation-workshop-latam
LAB_EVIDENCE_ENV='AWS CloudShell CCS' python3 booking_lab/run.py e2e --output .local/db-e2e.json
python3 scripts/workshop.py prepare --output .local/workshop-01
```

El runner consulta `MemoryLimit`, `CpuCfsQuota` y `PidsLimit` del daemon y guarda las capacidades declaradas en el JSON antes de decidir si aplica límites. La implementación anterior consultaba mal el nombre de CPU y podía registrar un falso negativo: los recibos históricos `resource_limits_available: false` demuestran que no se aplicaron esos límites, sin probar por sí solos que el host no los soportara. Los puertos de API solo se publican en `127.0.0.1`; la DB y pagos usan la red interna de Docker. Si reinicias un contenedor, consulta de nuevo el puerto asignado: puede cambiar.

## 3. Instala ATX si falta

Versión observada: ATX 3.19.0 con Node 22.23.3 en Linux x86_64. Consulta [la instalación oficial](https://docs.aws.amazon.com/transform/latest/userguide/custom.html) antes de actualizar versiones. Este bloque conserva el instalador para revisión y verifica el archivo de Node con su checksum oficial.

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
```

En cada terminal nueva vuelve a definir el PATH. `healthy` acredita la comprobación del CLI; cada análisis debe terminar y generar sus propios artefactos. Los análisis consumen [minutos de agente de Transform](https://aws.amazon.com/transform/pricing/).

## 4. Analiza y conserva evidencia

Continúa en [Ejecución AWS](EJECUCION_AWS.md). Usa Actions → Download file para descargar informes seleccionados y el JSON de DB. Conserva el código, commit, contexto y versión junto a los resultados. No publiques archivos `.env`, credenciales ni logs crudos sin revisar.

CloudShell tiene almacenamiento acotado. Si un build falla por espacio, inspecciona `df -h` y `docker system df`; elimina únicamente recursos de una práctica que hayas decidido descartar. El runner conserva sus datos de revisión y no ejecuta un prune global.

## Repetir sin agotar el disco de CloudShell

En CCS se observó el driver Docker `vfs`: los contenedores detenidos conservan copias completas de capas y el uso físico puede superar lo que parece indicar `docker system df`. Tras guardar y revisar una corrida, libera únicamente sus contenedores detenidos con el manifiesto que imprimió el runner:

```bash
python3 scripts/cleanup_lab.py --review .local/db-lab-ID/review.json
python3 scripts/cleanup_lab.py --review .local/db-lab-ID/review.json --remove-stopped
```

El primer comando muestra el alcance. El segundo conserva logs y volúmenes, rechaza cualquier contenedor activo y nunca usa `--force`, `--volumes` ni un prune global. Verifica `df -h /` antes de iniciar otra corrida. En un clon aislado de análisis, `review.json` estará dentro de su propia `.local/`; pasa esa ruta al mismo script.

## Persistencia y frontera del entorno

AWS documenta [cifrado en reposo para CloudShell](https://docs.aws.amazon.com/cloudshell/latest/userguide/data-encryption.html) y [almacenamiento persistente en `$HOME`](https://docs.aws.amazon.com/cloudshell/latest/userguide/limits.html). El volumen Docker del laboratorio vive en el almacenamiento del daemon: conserva los backups y la evidencia antes de que el entorno se recicle. El cifrado del servicio no sustituye permisos, rotación o archivo independiente de auditoría.

Las [preguntas de seguridad de AWS](https://docs.aws.amazon.com/cloudshell/latest/userguide/cloudshell-security-faqs.html) aclaran que el usuario de CloudShell dispone de root y que sus contenedores son una conveniencia operativa, no una frontera de seguridad frente a ese usuario. Por eso el E2E distingue el administrador SQL de la aplicación del administrador del host.
