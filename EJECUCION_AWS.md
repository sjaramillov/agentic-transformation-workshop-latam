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

Cada fuente debe mostrar `booking-mit`. Ambos clones contienen `booking_lab/` y `LICENSE` del mismo commit. El análisis cubre el servicio; las guías y la CI de la raíz se comprueban aparte.

## 2. D: ARA con escritura habilitada

```bash
atx ct analysis run --type agentic-readiness \
  --repo "$SOURCE_ARA::booking-mit" --source "$SOURCE_ARA" \
  --agent-scope write-enabled --context "$(cat "$PRACTICE/contexts/ara.txt")" \
  --json > "$PRACTICE/results/ara-run.log" 2>&1
cat "$PRACTICE/results/ara-run.log"
```

El contexto evalúa autorización por sujeto, pagos, saga, idempotencia y auditoría. Conserva el `analysisId` devuelto para consultar los resultados.

## 3. E: MODA sobre la misma base

```bash
atx ct analysis run --type modernization-readiness \
  --repo "$SOURCE_MODA::booking-mit" --source "$SOURCE_MODA" \
  --context "$(cat "$PRACTICE/contexts/moda.txt")" \
  --json > "$PRACTICE/results/moda-run.log" 2>&1
cat "$PRACTICE/results/moda-run.log"
```

El contexto pide el runtime compatible más sencillo. Puedes ejecutar D y E en dos terminales con el mismo PATH porque usan clones distintos.

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

El ejemplo usa una rúbrica ARA de 43 preguntas. Si tu versión tiene otra cobertura, revisa la rúbrica y ajusta `--expect-questions`. Después de verificar la estructura, revisa los hallazgos y contrástalos con las pruebas de la aplicación.

## 5. H: aplica una corrección revisable

Usa [la plantilla de decisión](workshop/templates/decision.md). Para una implementación manual crea una rama en un clon nuevo, corrige y ejecuta el E2E. También puedes publicar nuestra transformación original en tu cuenta:

```bash
atx custom def publish -n mit-booking-hardening-01 \
  --sd workshop/transformations/hardening \
  --description 'Correct verified Booking MIT findings and prove invariants' --category remediation
atx ct remediation create --repo "$SOURCE_ARA::booking-mit" --source "$SOURCE_ARA" \
  --transformation-name mit-booking-hardening-01 --name mit-booking-hardening-01 --local
```

Selecciona los hallazgos concretos en el contexto de la remediación según `atx ct remediation create --help`. Conserva el ID y consulta `atx ct remediation status --id ID --json`. Revisa la rama y diff exactos devueltos antes de integrar. Ejecuta las pruebas de la aplicación sobre esa rama antes de integrar.

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

## Si el análisis termina sin informes

Comprueba que la ejecución haya producido los artefactos JSON, Markdown, HTML y metadata. Un estado `complete` con cero hallazgos y sin esos archivos requiere revisar el log de la sesión y repetir el análisis sobre el mismo commit y contexto con un ID nuevo. Valida los artefactos de la nueva ejecución antes de comparar.

Como referencia opcional, consulta [un ejemplo de comparación ARA/MODA](CCS_E2E.md).
