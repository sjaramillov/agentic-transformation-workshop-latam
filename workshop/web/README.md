# Práctica web

**[Abrir con cliente y coach](https://sjaramillov.github.io/agentic-transformation-workshop-latam/practica/)**. Las personas que hacen el workshop solo necesitan un navegador.

## Cómo se mantiene

- `workshop/discovery.json` conserva las 21 situaciones y la progresión de los tres tableros.
- `scripts/build_site.py` genera `practica/course.js` con esos materiales, sus hashes y los contextos ARA/MODA.
- `engine.js` aplica las mismas reglas que `scripts/discovery.py`. Las pruebas comparan cada estado, respuesta, tablero y exportación en tres recorridos completos.
- `web.js` guarda el avance en el navegador, sincroniza pestañas y permite importar y descargar resultados. Los archivos no se envían a un servidor. Las descargas `session.json` pueden retomarse con el facilitador local.
- La interfaz y el renderizador de tableros se comparten con `workshop/coach/`. La práctica web utiliza archivos estáticos y no llama a AWS.

## Validar un cambio

Desde la raíz, con Python 3.11+ y Node 24+:

```bash
python3 -m unittest discover -s tests -v
cd web_tests
npm ci --ignore-scripts
npx playwright install chromium webkit
npm test
```

Playwright construye el sitio y recorre las 21 situaciones en Chromium, WebKit y una pantalla móvil. Comprueba ambas rutas de preguntas, ubicación progresiva de notas, cliente y coach, descargas, recuperación, importación, sesiones simultáneas, teclado y almacenamiento no disponible. Los resultados quedan en `.local/web-e2e/`.

Para comprobar la versión publicada con sesiones de prueba aisladas:

```bash
WORKSHOP_BASE_URL=https://sjaramillov.github.io/agentic-transformation-workshop-latam/ npm test
```

GitHub Actions publica Pages después de que pasen las pruebas Python, de base de datos y de navegador. El artefacto `browser-e2e-evidence` de cada ejecución contiene los resultados del recorrido.
