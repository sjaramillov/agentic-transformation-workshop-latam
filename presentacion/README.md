# Presentación del workshop

[Abrir la web](https://sjaramillov.github.io/agentic-transformation-workshop-latam/) · [Ver los tableros completos](../diagramas/README.md)

Ocho láminas para presentar el propósito, la conversación con cliente y coach, el proceso, los cuadrantes, el flujo, ARA/MODA, AI-DLC y los primeros pasos. Las seis ilustraciones resumidas usan notas y colores coherentes con los tableros; cada lámina enlaza el material para profundizar.

- Navega con **Anterior / Siguiente**, las flechas del teclado o el selector de lámina.
- Usa **Imprimir / PDF** para guardar las ocho láminas. En el diálogo de impresión, activa los gráficos de fondo y desactiva encabezados y pies del navegador.
- Cada lámina tiene su enlace directo, por ejemplo `#oportunidad`.
- Sin JavaScript se muestran todas las láminas en orden.

## Editar y previsualizar

Edita [index.html](index.html), [style.css](style.css) y [deck.js](deck.js). Las ilustraciones resumidas se generan desde [render_presentation.py](../scripts/render_presentation.py), que consulta las notas del discovery para los tableros A y B. Los tableros completos siguen usando su propio generador.

```bash
python3 scripts/render_presentation.py
python3 scripts/build_site.py
python3 -m http.server 8000 --bind 127.0.0.1 --directory .local/site
```

Abre `http://127.0.0.1:8000`. El sitio se publica en GitHub Pages después de superar los checks y las dos ejecuciones del E2E con base de datos. El constructor publica una selección explícita de materiales: presentación, ilustraciones, tableros completos y caso resuelto.

## Ayudas visuales

La ilustración de apertura muestra una conversación de discovery. Los diagramas SVG explican el caso de Booking MIT y se pueden descargar, editar y reutilizar. Consulta [los recursos visuales](../assets/README.md).
