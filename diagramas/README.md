# Tableros del workshop

Abre la [galería publicada](https://sjaramillov.github.io/agentic-transformation-workshop-latam/diagramas/), la [galería local](index.html) o guarda los SVG para usarlos en una sesión. Son materiales originales MIT, editables y sin dependencias externas.

La [presentación visual](https://sjaramillov.github.io/agentic-transformation-workshop-latam/) introduce el recorrido con ilustraciones resumidas y enlaza estos tableros completos.

| Tablero | Qué explica |
| --- | --- |
| [01 · Proceso](01-eventstorming.svg) | Dolores, eventos, personas, comandos, datos y reglas ubicados por momento del proceso. |
| [02 · Oportunidad](02-oportunidad-agente.svg) | Cuadrantes de criterio y datos; patrones A/P/E/G e intervención humana H. |
| [03 · Flujo](03-workflow-rebooking.svg) | Consultas, propuesta, aprobación, ejecución y recuperación en carriles. |
| [04 · ARA/MODA](04-ciclo-ara-moda.svg) | Hallazgo → prioridad → cambio → prueba → comparación. |
| [05 · Responsables](05-modelo-operativo.svg) | Decisiones y entregables de producto, aplicación, seguridad, plataforma y operación. |
| [06 · Valor y AI-DLC](06-valor-ai-dlc.svg) | Del dolor a una unidad de trabajo y un resultado medido. |

## Cómo se forman

Las láminas A–C muestran el estado final de los mismos datos que utiliza el coach en [discovery.json](../workshop/discovery.json). La [guía](../GUIA_REPLICACION.md) explica cómo aparecen y se ubican las notas en las 21 situaciones. El [ejemplo interactivo](../examples/discovery/tableros.html) conserva los tres tableros completos para consulta sin conexión.

- **A:** dolor en bandeja → límites → eventos → excepción → personas y comandos → reglas → información → prioridades → dependencias.
- **B:** candidatas → datos → cuadrantes → valor → intervención humana → patrón de autonomía.
- **C:** unidad → intención y datos → APIs → aprobación y ejecución → recuperación → contexto ARA/MODA.

Las posiciones son cualitativas. Cada color tiene un rótulo; los patrones de autonomía se acuerdan por acción. ARA/MODA aportan evaluación técnica y la ficha de valor organiza la medición del negocio.

## Editar y regenerar

Desde la raíz del repositorio:

```bash
python3 scripts/render_diagrams.py
python3 scripts/render_diagrams.py --check
```

El [generador](../scripts/render_diagrams.py) toma A–C del discovery y define las síntesis D–J. Conserva las rutas de los seis SVG para mantener los enlaces existentes.
