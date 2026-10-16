# Repetir el taller con el menor número de pasos

## Elige el recorrido

| Recorrido | Necesita | Qué comprueba |
| --- | --- | --- |
| Leer y ver diagramas | Este repositorio | Conceptos y secuencia A–J |
| **Práctica local recomendada** | Python 3.11+, Bash y la captura autorizada | Restauración, A–C, contextos e informes capturados |
| Ejecución AWS | Entorno del evento o cuenta preparada, ATX, Kiro, permisos y modelos | Nuevos análisis y remediaciones D–I |

La práctica local está probada de extremo a extremo. La ejecución AWS completa está pendiente: una clasificación ARA/MODA no demuestra que el servicio esté desplegado o funcione en producción. Consulta [la auditoría y sus límites](AUDITORIA_E2E.md).

## 1. Clona la guía

En una terminal Bash de macOS o Linux:

```bash
git clone https://github.com/sjaramillov/agentic-transformation-workshop-latam.git
cd agentic-transformation-workshop-latam
export REPLICA_DIR="$PWD"
python3 --version
```

Necesitas Python **3.11 o posterior**. No hay paquetes pip que instalar para nuestros scripts ni para A–C offline. Windows necesita un entorno Linux como WSL; ese entorno no se probó en esta revisión.

## 2. Restaura la captura en una carpeta nueva

El archivo original no se distribuye en GitHub porque no se identificó una licencia para redistribuir TravelCorp. Obtén el paquete por el canal autorizado del taller. La captura del autor se conserva en la carpeta local del proyecto, bajo `resources/agentic-workshop-materials-2026-10-15.tar.gz`.

Configura `WORKSHOP_ARCHIVE` con la ruta real del archivo. Este ejemplo funciona si ya lo colocaste en `resources/` de este clon:

```bash
export WORKSHOP_ARCHIVE="$REPLICA_DIR/resources/agentic-workshop-materials-2026-10-15.tar.gz"
export LAB_ENV="$REPLICA_DIR/.local/environment"

python3 scripts/lab.py restore \
  --archive "$WORKSHOP_ARCHIVE" --destination "$LAB_ENV"
python3 scripts/lab.py doctor --environment "$LAB_ENV"
```

`restore` verifica el SHA-256 de [CHECKSUMS.txt](CHECKSUMS.txt), rechaza rutas inseguras y enlaces, y conserva el contenido en un destino nuevo. Si el archivo es una **captura diferente autorizada**, pasa `--sha256 HASH_VERIFICADO` calculado y contrastado con su fuente. Cambiar el hash solo acepta otro archivo; no certifica su contenido ni su compatibilidad.

**Criterio de éxito:** `doctor` termina con código 0 y `"ok": true`. Si el destino existe, se rechaza: usa una carpeta nueva para repetir; no hace falta borrar tu trabajo.

## 3. Ejecuta A–C offline

```bash
python3 scripts/lab.py rehearse \
  --environment "$LAB_ENV" --output "$REPLICA_DIR/.local/practica-01"
```

El comando copia el facilitador a un directorio nuevo y ejecuta tres fases con `--offline`. Las respuestas están escritas de antemano; no invoca Bedrock, Kiro ni ATX. Las opciones de facilitación afectan la conversación y el feedback, pero el escenario capturado genera el mismo diseño de rebooking/P.

**Criterio de éxito:** código 0 y `rehearsal.json` con `candidate: rebooking`, `autonomy: P`, ocho artefactos y sus hashes. Encontrarás:

```text
.local/practica-01/
  exercises/eventstorm-output.md + eventstorm-board.json
  exercises/quadrant-output.md + quadrant-board.json
  exercises/workflow-design-output.md
  atx-config-ara.yaml
  atx-config-mod.yaml
  run-manifest.json
  context-ara.txt + context-mod.txt
  phase-1.log + phase-2.log + phase-3.log
  rehearsal.json
```

Para practicar interactivamente, entra en `.local/practica-01/exercises` y ejecuta `python3 -m agentstorming.facilitate --phase 1 --offline`; continúa con fases 2 y 3. Esto actualiza los tableros de esa práctica. El archivo original y el entorno restaurado se mantienen como referencia.

## 4. Recupera los informes con su procedencia

```bash
python3 scripts/lab.py collect --environment "$LAB_ENV" \
  --origin captured --output "$REPLICA_DIR/.local/informes-capturados-01"
python3 scripts/lab.py collect --environment "$LAB_ENV" \
  --origin precomputed --output "$REPLICA_DIR/.local/baseline-01"
```

Cada carpeta contiene `inventory.json`, los hashes y la ruta de origen de cada archivo. Los informes que estaban en `reports/` y los que estaban dentro de un servicio conservan rutas distintas. No se elige un informe por fecha ni se mezcla con el baseline. Ninguna de estas copias es un análisis nuevo. Lee primero JSON y Markdown; un HTML puede corresponder a una corrida anterior.

Los comandos no abren puertos, no borran reportes y no terminan procesos. El script original `consolidate-reports.sh` sí puede hacer esas tres cosas; resérvalo al IDE del taller y respalda antes sus informes.

## 5. Repite la verificación

```bash
python3 -m unittest discover -s tests -v
WORKSHOP_ARCHIVE="$WORKSHOP_ARCHIVE" python3 -m unittest discover -s tests -v
```

Sin `WORKSHOP_ARCHIVE`, la prueba que necesita el archivo privado se marca **skipped**. Con la captura conocida, también restaura un entorno temporal desde cero, ejecuta A–C, verifica contextos y recolecta informes de ambos orígenes. Las pruebas no llaman AWS.

## 6. Continuar en AWS

Sigue [EJECUCION_AWS.md](EJECUCION_AWS.md), después [GUIA_REPLICACION.md](GUIA_REPLICACION.md) para la interpretación de cada módulo. El script local no instala ATX, no concede IAM y no reconstruye la plantilla del evento. No exportes tus credenciales a este repositorio.

## Si algo falla

| Síntoma | Acción |
| --- | --- |
| `No such file` al restaurar | Corrige `WORKSHOP_ARCHIVE`; un clon público no contiene ese archivo. |
| SHA-256 diferente | Revisa origen y descarga; no cambies el hash para ocultar una corrupción. |
| Destino ya existe | Usa `practica-02`, `environment-02` o un nombre nuevo. |
| Falló fase A–C | Lee `phase-N.log` en la salida; revisa Python y la integridad del paquete. |
| Falta un contexto | Ejecuta las fases 1, 2 y 3 en orden y en el mismo directorio. |
| `doctor --live` falla por rama | La captura contiene una rama temporal; sigue la preparación Git en la guía AWS. |
| No hay informes capturados | Revisa si la ejecución concluyó y dónde guardó sus artefactos; el recolector no inventa resultados. |
