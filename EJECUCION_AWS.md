# ARA, MODA y remediación sobre Booking MIT

Prerrequisitos: [CloudShell preparado](CLOUDSHELL.md), ATX disponible y acceso autorizado a Transform. Todo el código de entrada está en el repo. El análisis administrado requiere tu cuenta AWS y genera resultados nuevos.

## 1. Selecciona un conjunto trazable

Desde la raíz del clon público, reutiliza `.local/workshop-01`, preparado en Inicio rápido o CloudShell. El bloque lo crea solo si todavía no existe. La revisión analizada es la que registra su `manifest.json`; preparar no incorpora cambios sin commit. Si ese directorio ya contiene resultados de análisis, elige otro nombre para `PRACTICE` y sufijos nuevos para las fuentes antes de ejecutar el bloque. `mkdir results` evita sobrescribir una corrida anterior.

```bash
set -euo pipefail
export PRACTICE="$(pwd)/.local/workshop-01"
if [ ! -e "$PRACTICE" ]; then
  python3 scripts/workshop.py prepare --output "$PRACTICE"
fi
test -f "$PRACTICE/manifest.json"
test -f "$PRACTICE/contexts/ara.txt"
test -f "$PRACTICE/contexts/moda.txt"
test -d "$PRACTICE/sources/ara/booking-mit/.git"
test -d "$PRACTICE/sources/moda/booking-mit/.git"
mkdir "$PRACTICE/results"
export AWS_REGION=us-east-1
# Elige un sufijo nuevo para cada comparación.
export SOURCE_ARA=mit-ara-01
export SOURCE_MODA=mit-moda-01
atx --version
atx ct status --health
atx ct source add --name "$SOURCE_ARA" --provider local --path "$PRACTICE/sources/ara"
atx ct discovery scan --source "$SOURCE_ARA"
atx ct source add --name "$SOURCE_MODA" --provider local --path "$PRACTICE/sources/moda"
atx ct discovery scan --source "$SOURCE_MODA"
atx ct repository list --source "$SOURCE_ARA"
atx ct repository list --source "$SOURCE_MODA"
```

Cada fuente debe mostrar `booking-mit`. Los dos clones contienen el mismo commit. El alcance de esta comparación es el servicio. La CI y las guías de la raíz se verifican aparte; los informes pueden señalar su ausencia en el clon reducido. No interpretes esa ausencia como falta de CI en el repo público. No registres informes históricos como código de entrada: el preparador selecciona `booking_lab/` y `LICENSE` del commit indicado, registra hashes y excluye secretos y resultados anteriores.

## 2. D: ARA con escritura habilitada

```bash
atx ct analysis run --type agentic-readiness \
  --repo "$SOURCE_ARA::booking-mit" --source "$SOURCE_ARA" \
  --agent-scope write-enabled --context "$(cat "$PRACTICE/contexts/ara.txt")" \
  --json > "$PRACTICE/results/ara-run.log" 2>&1
cat "$PRACTICE/results/ara-run.log"
```

El contexto exige evaluar autorización por sujeto, pagos, saga, idempotencia y auditoría. No ordena excluir problemas de producción ni declarar madurez por ser un ejemplo. Conserva el `analysisId` devuelto.

## 3. E: MODA sobre la misma base

```bash
atx ct analysis run --type modernization-readiness \
  --repo "$SOURCE_MODA::booking-mit" --source "$SOURCE_MODA" \
  --context "$(cat "$PRACTICE/contexts/moda.txt")" \
  --json > "$PRACTICE/results/moda-run.log" 2>&1
cat "$PRACTICE/results/moda-run.log"
```

La práctica no presupone un clúster EKS. El contexto pide el runtime compatible más sencillo. Puedes ejecutar D y E en dos terminales con el mismo PATH porque usan clones distintos.

## 4. F–G: inspecciona y prioriza

```bash
# Sustituye ID por el ID exacto de tu ejecución.
atx ct analysis get --id ID --json
# Si necesitas detener esa ejecución:
# atx ct analysis cancel --id ID
```

Espera `complete`/`completed` y localiza los informes JSON, Markdown, HTML y metadata en la salida de esa ejecución. No elijas el informe más reciente de otra fuente. Valida el conjunto:

```bash
python3 scripts/verify_reports.py RUTA_AL_INFORME_ARA.json --kind ara --expect-questions 43
python3 scripts/verify_reports.py RUTA_AL_INFORME_MODA.json --kind mod
```

Las 43 preguntas corresponden a la rúbrica ARA observada. Si AWS cambia la rúbrica, revisa cobertura y versión; no cambies el número únicamente para conseguir una validación verde. El verificador contrasta estructura y conteos; la revisión de cada juicio y la prueba funcional son pasos adicionales.

## 5. H: aplica una corrección revisable

Usa [la plantilla de decisión](workshop/templates/decision.md). Para una implementación manual crea una rama en un clon nuevo, corrige y ejecuta el E2E. También puedes publicar nuestra transformación original en tu cuenta:

```bash
atx custom def publish -n mit-booking-hardening-01 \
  --sd workshop/transformations/hardening \
  --description 'Correct verified Booking MIT findings and prove invariants' --category remediation
atx ct remediation create --repo "$SOURCE_ARA::booking-mit" --source "$SOURCE_ARA" \
  --transformation-name mit-booking-hardening-01 --name mit-booking-hardening-01 --local
```

Selecciona los hallazgos concretos en el contexto de la remediación según `atx ct remediation create --help`. Conserva el ID y consulta `atx ct remediation status --id ID --json`. Revisa la rama y diff exactos devueltos antes de integrar. Esta TD contiene instrucciones originales; una ejecución satisfactoria requiere pruebas, no solo una rama generada.

## 6. I–J: vuelve a medir y publica evidencia

Registra los cambios revisados en un commit de tu repositorio antes de preparar las nuevas fuentes. `prepare --revision HEAD` extrae archivos comprometidos en Git; deja fuera cambios sin commit. Ejecuta las pruebas y el análisis sobre esa misma revisión:

```bash
python3 -m unittest discover -s tests -v
python3 booking_lab/run.py e2e --output .local/db-after.json
export PRACTICE="$(pwd)/.local/workshop-02"
python3 scripts/workshop.py prepare --output "$PRACTICE" --revision HEAD
export SOURCE_ARA=mit-ara-02
export SOURCE_MODA=mit-moda-02
mkdir "$PRACTICE/results"
atx ct source add --name "$SOURCE_ARA" --provider local --path "$PRACTICE/sources/ara"
atx ct discovery scan --source "$SOURCE_ARA"
atx ct source add --name "$SOURCE_MODA" --provider local --path "$PRACTICE/sources/moda"
atx ct discovery scan --source "$SOURCE_MODA"
atx ct repository list --source "$SOURCE_ARA"
atx ct repository list --source "$SOURCE_MODA"
```

Con esas variables actualizadas, repite los comandos D/E de las secciones 2 y 3. Usa nombres nuevos si `.local/workshop-02` o esas fuentes ya existen. Comprueba los hashes de contexto de ambos `manifest.json`: si cambió el contexto, registra esa diferencia antes de interpretar el resultado. Compara por pregunta con [la plantilla CSV](workshop/templates/comparison.csv) o genera JSON y CSV automáticamente:

```bash
python3 scripts/compare_reports.py ANTES_ARA.json DESPUES_ARA.json \
  --kind ara --expect-questions 43 --output .local/comparison-ara
python3 scripts/compare_reports.py ANTES_MODA.json DESPUES_MODA.json \
  --kind mod --output .local/comparison-moda
```

El comparador valida los cuatro artefactos, preserva las etiquetas del evaluador y marca preguntas ausentes. Una pregunta antes no evaluada que pasa después no equivale por sí sola a una corrección de código. Conserva los informes completos, sus hashes, los commits de fuente y prueba, los conteos y la justificación de cada cierre. Revisa información sensible antes de publicar resultados.

Consulta [la comparación real de CCS](CCS_E2E.md) y [la prueba con DB](CCS_DATABASE_E2E.md). El análisis y el runtime tienen evidencias distintas; ambos forman parte de la aceptación.

## Diagnóstico: `complete` con cero hallazgos y sin informe

En ATX 3.19.0 se observó una ejecución MODA cuyo agente terminó con `An internal server error occurred`, mientras CT devolvió `complete` y `findingCount: 0`. No era un resultado limpio: faltaban los cuatro artefactos. Conserva la metadata y logs de esa sesión en privado, registra el intento como fallido en tu evidencia y repite sobre el mismo commit/contexto con un ID nuevo. Acepta la repetición únicamente al validar los artefactos. La comparación de [CCS](CCS_E2E.md) identifica este incidente.

## Repetir el antes y después publicado

Los dos estados de la aplicación están disponibles en el historial público. Desde un clon normal, prepara ambos usando el mismo script y los mismos contextos:

```bash
python3 scripts/workshop.py prepare --revision e338a6b99cba389cbb5d96ca21a12d660071b28d \
  --output .local/reproduce-before
python3 scripts/workshop.py prepare --revision 401e5317567f3500843bc722893bf6d22b733390 \
  --output .local/reproduce-after
```

Registra fuentes con nombres distintos y repite D/E para cada directorio. Los commits de los clones nuevos pueden diferir por su fecha de creación; compara `source_sha256` y `context_sha256` de sus manifiestos. La aplicación posterior debe coincidir con [los hashes publicados](evidence/mit/source-sha256.json). Las definiciones administradas y los juicios de AWS pueden cambiar, por lo que no se promete una puntuación idéntica.
