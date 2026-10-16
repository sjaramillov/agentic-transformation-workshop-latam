# Recorrido AWS: preparación y criterios de aceptación

Este recorrido ejecuta servicios AWS y puede generar cargos. Se contrastaron comandos con la guía del evento, con `--help` del ATX instalado y con documentación oficial. La [ejecución posterior en CCS](CCS_E2E.md) registra qué pasos se ejecutaron y qué fallos se observaron. El evento tenía ATX 3.9.0 y CCS utilizó 3.19.0; conserva la versión junto a los resultados.

## 1. Entorno y acceso

La opción más directa es continuar en el IDE ya preparado del evento mientras esté vigente. Para una cuenta propia necesitas la preparación oficial de [continuous modernization](https://docs.aws.amazon.com/transform/latest/userguide/ct-getting-started.html): Node.js 22+, ATX, credenciales válidas y permisos de AWS Transform. El facilitador **en vivo** además necesita Strands, boto3 y acceso a sus modelos Bedrock; A–C offline evita esa dependencia. Kiro se prepara según [su documentación](https://kiro.dev/docs/cli/).

La plantilla `VsCodeServerIDE` y la política IAM del evento **no están en esta copia**. Una cuenta nueva no queda lista solo con restaurar el tar. Puedes usar ejecución local de ATX en un equipo compatible preparado con la guía oficial; Batch/EKS no son requisitos para ejecutar los análisis locales. EKS aparece como destino de diseño de la remediación, no como un clúster que esta réplica haya creado.

En el evento se usó `us-east-1` y Quick start para la aplicación web. En una cuenta propia define primero el acceso y almacenamiento con sus responsables. No sustituyas esa decisión por los valores del evento. Instala ATX solo si falta; en el IDE evita reemplazar la versión preinstalada sin revisar compatibilidad.

El procedimiento observado para una cuenta propia está en [CLOUDSHELL.md](CLOUDSHELL.md). Antes de ejecutar H, revisa los hallazgos sobre las definiciones originales en [LIMITACIONES_TD.md](LIMITACIONES_TD.md).

## 2. Fija rutas y revisa el estado

Ejecuta los ejemplos en **Bash**. En el IDE:

```bash
export LAB_ENV="$HOME/environment"
export PORTFOLIO="$LAB_ENV/apps/travelcorp-portfolio"
export AWS_REGION=us-east-1
atx --version
node --version
kiro-cli --version
aws --version
git --version
jq --version
python3 --version
```

En una restauración local, asigna `LAB_ENV` al destino de `restore`. `REPLICA_DIR` debe apuntar al clon de esta guía:

```bash
python3 "$REPLICA_DIR/scripts/lab.py" doctor --environment "$LAB_ENV" --live
```

Este chequeo es local: no valida identidad, IAM, cuota ni disponibilidad del modelo. Para AWS, comprueba en privado la identidad con `aws sts get-caller-identity` y `atx ct status --health`. Conserva las versiones junto a tus resultados; no publiques identificadores de cuenta ni credenciales.

`doctor --live` revisa la preparación completa del IDE, incluidos Kiro y los tres servicios. La ruta reducida de [CloudShell](CLOUDSHELL.md) usa ATX directamente y una copia adicional de un servicio; sigue sus comprobaciones específicas. Kiro no fue necesario para esas ejecuciones de ATX.

## 3. Prepara los repositorios

La captura del 15 de octubre conserva `booking-service` en `atx-result-staging-20261015_183919_02db4098`, que contiene informes de análisis. El archivo comprimido conserva la evidencia original. Antes de una nueva ejecución, recolecta sus informes con `lab.py collect`, y revisa:

```bash
for service in booking-service notification-service payment-gateway; do
  git -C "$PORTFOLIO/src/$service" status --short --branch
  git -C "$PORTFOLIO/src/$service" log -3 --oneline
done
```

En una **copia recién restaurada y limpia**, cambia los tres a `main`:

```bash
for service in booking-service notification-service payment-gateway; do
  git -C "$PORTFOLIO/src/$service" switch main || break
done
```

No integres una rama de análisis como si fuera una remediación. Si hay cambios locales, consérvalos y revísalos antes de continuar. El detector espera `.git/` dentro de cada subdirectorio de `src/`.

## 4. Registra la fuente y genera el contexto

```bash
atx ct repository list --source travelcorp
# Solo si no está configurada en este equipo:
atx ct source add --name travelcorp --provider local --path "$PORTFOLIO/src"
atx ct discovery scan --source travelcorp
atx ct repository list --source travelcorp
```

**Éxito:** aparecen exactamente los tres slugs `travelcorp::booking-service`, `travelcorp::notification-service` y `travelcorp::payment-gateway`. Si ya existe una fuente `travelcorp` con otros repositorios, detente y elige un nombre distinto en todos los comandos; no reutilices accidentalmente otra cartera.

Para generar contexto sin consumir modelos:

```bash
cd "$PORTFOLIO/exercises"
python3 -m agentstorming.facilitate --phase 1 --offline --choices 1,1,1,1,1,1,1,1,1,1
python3 -m agentstorming.facilitate --phase 2 --offline --choices 1,1,1,1,1,1,1,1,1,1
python3 -m agentstorming.facilitate --phase 3 --offline --choices 1,1,1,1,1,1,1,1,1,1
bash ./build-atx-context.sh ara
bash ./build-atx-context.sh mod
```

**Éxito:** ambos contextos tienen texto sobre Rebooking y autonomía P. Los YAML y `run-manifest.json` quedan en `$PORTFOLIO`; los tableros quedan en `$PORTFOLIO/exercises`.

## 5. Analiza D–E y conserva IDs

Registra el ID devuelto, commit de `main`, contexto, alcance y versión. Ejecuta MODA cuando ARA termine. La comprobación previa del contexto evita lanzar un análisis genérico por un archivo ausente:

```bash
ARA_CONTEXT="$(bash "$PORTFOLIO/exercises/build-atx-context.sh" ara)"
test -n "$ARA_CONTEXT" &&
atx ct analysis run --type agentic-readiness \
  --repo travelcorp::booking-service --source travelcorp \
  --agent-scope write-enabled --context "$ARA_CONTEXT"
```

Después de confirmar la finalización de ARA:

```bash
MOD_CONTEXT="$(bash "$PORTFOLIO/exercises/build-atx-context.sh" mod)"
test -n "$MOD_CONTEXT" &&
atx ct analysis run --type modernization-readiness \
  --repo travelcorp::booking-service --source travelcorp \
  --context "$MOD_CONTEXT" --prefer eks \
  --avoid self-managed-mysql,manual-deployments,monolith-in-place
```

```bash
# Sustituye ID por el identificador devuelto, no por la primera fila del listado.
atx ct analysis get --id ID --json
```

**Éxito:** el ID correcto corresponde a la fuente, repositorio y tipo esperados, tiene estado final satisfactorio y artefactos JSON/Markdown. Un rollup de portafolio y un informe de repositorio son resultados distintos. Un archivo presente o un contador de minutos no bastan para declarar completa una ejecución.

Conserva capturas antes y después en directorios nuevos usando `lab.py collect`. El recolector busca el directorio `reports/` y los artefactos del árbol de servicios, **no** el almacén interno `~/.atxct`. Si ATX solo guardó la nueva ejecución allí, recupera la ruta del ID de ejecución y copia ese conjunto explícitamente; no uses el HTML anterior como sustituto. El inventario local preserva archivos, pero no certifica cuál corresponde a ese ID.

## 6. Publica las TD y aplica H

Lee primero ambos `SKILL.md`. Estos comandos publican definiciones en tu cuenta; no los uses como un chequeo de conectividad. El siguiente bloque adapta la categoría a la opción disponible en el CLI:

```bash
publish_options=()
if atx custom def publish --help | grep -q -- '--category'; then
  publish_options=(--category remediation)
fi
atx custom def publish -n workshop-containerize-to-eks \
  --sd "$PORTFOLIO/custom-td-containerize" \
  --description "Workshop: containerizar PHP/Apache para EKS" "${publish_options[@]}"
atx custom def publish -n workshop-booking-service-fix-blockers \
  --sd "$PORTFOLIO/custom-td" \
  --description "Workshop: resolver bloqueadores del agente de rebooking" "${publish_options[@]}"
atx custom def list
```

En ATX 3.9.0 se comprobó `-n`, `--sd` y `--description`; su ayuda no incluye `--category`. Las versiones que exponen la categoría deben registrar estas TD como `remediation`. No ocultes errores con `2>/dev/null || true`; volver a publicar puede crear otra versión, no es una operación necesariamente vacía.

Aplica las remediaciones H de la guía sobre una copia limpia. Para `-g`, usa una ruta absoluta independiente de tu directorio de trabajo:

```bash
atx ct remediation create --repo travelcorp::booking-service --source travelcorp \
  --transformation-name workshop-containerize-to-eks --name containerize --local
```

Espera el resultado, revisa e integra la primera remediación antes de ejecutar la segunda sobre el mismo repositorio:

```bash
test -s "$PORTFOLIO/atx-config-ara.yaml" &&
atx ct remediation create --repo travelcorp::booking-service --source travelcorp \
  --transformation-name workshop-booking-service-fix-blockers \
  --name fix-auth-blockers -g "file://$PORTFOLIO/atx-config-ara.yaml" --local
```

Conserva el ID de remediación y consulta `atx ct remediation status --id ID --json`. Obtén de esa ejecución la rama exacta y comprueba su diff. **No selecciones automáticamente la rama más nueva**: el mismo repositorio puede contener ramas de análisis o remediaciones previas.

Para la ruta de contenedores, el ejercicio también cambia el destino declarado en IaC. Después de revisar e integrar la rama correcta, y todavía en una copia de práctica:

```bash
cd "$PORTFOLIO/src/booking-service"
cp "$PORTFOLIO/platform-team/deploy-pipeline.yaml" infrastructure/deploy-pipeline.yaml
cp "$PORTFOLIO/platform-team/booking-service-eks.yaml" infrastructure/booking-service.yaml
git diff -- infrastructure/
```

Estas copias modifican dos archivos locales. La plantilla de pipeline capturada falla dos reglas de cfn-lint (fuente vacía y artefacto de entrada ausente); consulta [la validación ejecutada](LIMITACIONES_TD.md). Se usa aquí como declaración de arquitectura del ejercicio y requiere completar sus conexiones antes de cualquier despliegue. Revisa antes de confirmar el commit. El pipeline contiene supuestos de plataforma, permisos y recursos: cambiar IaC para que un analizador detecte EKS no demuestra que `cluster-x` exista ni que un deploy haya funcionado.

## 7. Aceptación de I y de un despliegue real

Repite discovery y los análisis sobre `main`, manteniendo contexto y alcance. Guarda IDs, hashes y diffs de hallazgos; la salida de las TD es variable. No exijas un tier predeterminado ni ajustes código solo para hacer desaparecer una etiqueta.

Para certificar un servicio desplegado también harían falta: build de la imagen, validación de IaC, autenticación positiva/negativa, reintentos idempotentes, compensación ante fallos, comprobación de PII, callback humano con timeout/rechazo, logs y rollback. En CCS se ejecutaron build, sintaxis PHP, HTTP sin DB y cfn-lint; consulta [los resultados](CCS_E2E.md). **Las pruebas completas del despliegue de ese PHP siguen pendientes.** La [réplica original MIT](CCS_DATABASE_E2E.md) ya valida los escenarios de negocio con PostgreSQL en CCS. El taller diseña el workflow; no entrega un agente de rebooking desplegado por completar A–I.

## 8. Cierre

Respalda definiciones, commits e informes antes de que expire la cuenta. En una cuenta propia, inventaría todas las pilas creadas (IDE, ATX remoto si se usó y posibles despliegues). Borrar solo `VsCodeServerIDE` no demuestra que todo el consumo haya terminado. Usa la limpieza oficial correspondiente y confirma los recursos restantes.
