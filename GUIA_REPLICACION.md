# Del dolor del proceso a un agente: guía paso a paso

Tú facilitas una reunión de **Booking MIT**, un servicio de reservas. Elena representa producto; Mateo, operaciones; Lucía, ingeniería; Nora, seguridad. Empieza escuchando qué les cuesta trabajo. El cliente y el coach responden a preguntas preparadas y los tableros se construyen con cada situación.

**El recorrido:** dolores → proceso → oportunidad → autonomía → flujo → ARA/MODA → cambio probado → medición de valor.

Para presentar el recorrido a tu equipo, abre la [presentación visual](https://sjaramillov.github.io/agentic-transformation-workshop-latam/): ocho láminas con ilustraciones, enlaces a los tableros y opción de imprimir como PDF.

## 1. Abre el workshop

**[Entrar a la práctica web](https://sjaramillov.github.io/agentic-transformation-workshop-latam/practica/)**. Solo necesitas un navegador. Las preguntas, el cliente, el coach y los tableros funcionan directamente allí, sin clonar el repo ni instalar Python.

En cada situación:

1. Lee lo que ocurre y elige la pregunta que harías.
2. Escucha al cliente y revisa el feedback del coach.
3. Mira las notas nuevas y su ubicación. **Ampliar tablero** permite ver todo el mapa; también puedes desplazarlo horizontalmente.
4. Pulsa **Siguiente situación**. Puedes volver a ver los tableros A, B y C usando sus botones.

El coach valora la pregunta elegida. Cuando hace falta información, aporta una síntesis para que puedas continuar; las distintas elecciones llegan al mismo caso de aprendizaje.

### Pausar, retomar o guardar

Puedes cerrar la pestaña y volver: el avance se guarda automáticamente en el mismo navegador, incluso mientras lees el feedback. En **Tu avance** encontrarás:

- **Descargar avance:** guarda `session.json` con tus elecciones y el punto del recorrido.
- **Cargar avance:** elige ese archivo para retomar en otro navegador; confirma antes de reemplazar la sesión actual.
- **Nueva práctica:** empieza desde la primera pregunta.

Al completar C también puedes descargar `resumen.md`, los tres tableros en `tablero.html` (se abren sin conexión) y los contextos `ara.txt` y `moda.txt`. Si tu navegador impide guardar datos, la página lo indica y puedes continuar descargando el avance antes de salir. Borrar los datos del sitio también elimina el progreso guardado en él.

<details>
<summary>Opcional: preparar el laboratorio local para ejecutar el agente</summary>

Cuando quieras ejecutar el código del laboratorio, necesitas Git y Python 3.11+ en Linux, macOS o WSL:

```bash
git clone https://github.com/sjaramillov/agentic-transformation-workshop-latam.git
cd agentic-transformation-workshop-latam
```

Para llevar tu avance web al laboratorio, crea la carpeta `.local/discovery-01/` y copia allí el archivo descargado `session.json`. También puedes comenzar o retomar la práctica local con:

```bash
python3 scripts/facilitate.py
```

Abre la URL de la terminal y mantenla abierta. `Ctrl+C` pausa el servidor; el mismo comando retoma. La sesión, conversación y tableros quedan en `.local/discovery-01/`; los contextos se generan en su subcarpeta `contexts/` al completar C.

Para otra persona: `python3 scripts/facilitate.py --output .local/discovery-02`. Ambas modalidades comprueban la versión de los materiales al cargar un avance; conserva tu archivo si necesitas retomarlo con una versión anterior.

</details>

## 2. Entiende el dolor y el proceso (A)

**Abre con un incidente concreto:** una persona intenta reservar, se pierde la respuesta y no sabe si ya se cobró. Antes de proponer tecnología, averigua qué pasó y quién tuvo que resolverlo.

| Situación | Qué buscas entender | Cómo cambia el tablero |
| --- | --- | --- |
| A1 · Un caso real | Qué se atascó y qué incertidumbre dejó | El primer dolor entra en la bandeja por ubicar |
| A2 · Límites | Dónde empieza y cuándo se considera resuelto | Aparecen inicio y condición de cierre |
| A3 · Caso habitual | Qué sucedió, en qué orden | Solicitud → aprobación → pago → reserva |
| A4 · Excepción | Respuesta perdida frente a fallo tras el cobro | El dolor se ubica bajo recuperación; se añade conciliación o compensación |
| A5 · Personas | Quién solicita, confirma y recupera | Personas y comandos alineados con los eventos |
| A6 · Reglas y criterio | Qué es una regla y qué necesita interpretación | Políticas bajo los pasos: si ocurre X, ejecutar Y |
| A7 · Información | Qué datos usa cada decisión y cuáles faltan | Post-it de información junto a su paso |
| A8 · Prioridad | Qué cuesta tiempo y qué obliga a detenerse | Dolores y condiciones de parada en su lugar |
| A9 · Dependencias | Qué sistemas sostienen el proceso | API, DB, pagos y worker al pie del mapa |

**Cómo leer A:** cada columna representa un momento. Sus filas conectan persona → comando → información → evento → regla → dolor. El tramo de recuperación está separado por una línea discontinua. Los eventos describen algo que ya ocurrió; los comandos describen lo que alguien pide hacer.

**Antes de seguir, debes poder explicar:** por qué una respuesta perdida no autoriza un segundo cobro y cuándo corresponde compensar el primero.

## 3. Elige la oportunidad y diseña el flujo (B–C)

### B · Ubica las oportunidades

En seis situaciones identificarás tareas, comprobarás datos, compararás alternativas, acordarás una métrica, delimitarás la aprobación y cerrarás el alcance.

El cuadrante tiene dos ejes:

| | Reglas conocidas | Interpretación y criterio |
| --- | --- | --- |
| **Datos disponibles** | Considerar automatización convencional | Considerar asistencia con agente |
| **Datos por habilitar** | Integrar datos antes de automatizar | Preparar fuentes y permisos antes del piloto |

Las candidatas aparecen en una bandeja. Después de revisar datos y alternativas, pasan a sus cuadrantes. El formulario queda en reglas/datos disponibles; explicar o preparar una reserva, en criterio/datos disponibles; las excepciones comerciales, en criterio/datos pendientes.

La autonomía se acuerda después de ubicar la oportunidad:

- **A:** autonomía completa.
- **P:** el agente prepara una decisión y espera aprobación.
- **E:** exploración asistida por el agente.
- **G:** el agente actúa como control o guardrail.
- **H:** intervención humana obligatoria.

Para las escrituras del caso elegimos **P + H**. Crear y cancelar requieren aprobaciones independientes. Estas letras describen patrones de actuación; no son una escala que debas completar.

Completa la [ficha de valor](FICHA_VALOR.md) cuando el coach llegue a B4. El caso utiliza **200 casos/mes, 8 minutos humanos por caso y una meta de 6**, como supuestos para practicar. Compara formulario, asistente de consulta y agente con aprobación; incluye revisión, recuperación, errores y costo.

### C · Construye el recorrido por carriles

Las seis situaciones delimitan: unidad de trabajo → intención y entradas → consultas y acciones → aprobación → recuperación → entrega a ARA/MODA.

El tablero coloca las notas bajo **Externo/API, Datos, Agente y Persona**, en columnas numeradas. Sigue los cambios de carril:

1. El usuario expresa su intención.
2. El agente reúne datos y consulta reservas propias. Si falta información, aclara o se detiene.
3. Prepara una propuesta con datos explícitos.
4. La persona aprueba o rechaza. Rechazo significa fin sin escritura.
5. La API valida identidad, permisos y aprobación antes de crear o cancelar.
6. Se consulta el resultado, se retoma la misma operación si hace falta y se conserva auditoría.

Bajo el flujo aparece el mapa de aplicaciones y sus puntos de contacto: `GET /bookings` y `GET /bookings/{id}` son lecturas; `POST /bookings` y `DELETE /bookings/{id}` producen efectos. El backend implementa creación y cancelación con pagos sintéticos.

**Cierre de C:** deberías poder señalar el dolor, la alternativa elegida, quién aprueba, qué API toca el agente y cómo se recupera una respuesta incierta. El coach genera los contextos para que esos requisitos lleguen a los análisis.

## 4. Lee ARA con el caso en mente (D)

ARA evalúa las aplicaciones con las que interactúa el agente. Puede estudiarlas individualmente, como dependencias de un workflow o como portafolio. La metodología aborda cinco áreas: interfaces, identidad y acceso, datos, resiliencia y observabilidad. [Método de AWS](https://aws.amazon.com/blogs/migration-and-modernization/agentic-readiness/).

En la rúbrica de referencia, esos pilares se desarrollan en ocho secciones: API, identidad, estado, supervisión humana, datos, descubrimiento de contratos, observabilidad e ingeniería. El discovery prepara el caso; la evaluación técnica busca evidencia de sus controles.

En este caso el flujo C delimita la superficie: una aplicación con estado y operaciones de lectura y escritura. ARA utiliza el arquetipo y el alcance para seleccionar preguntas y valorar los hallazgos. La configuración del ejercicio es `agent_scope: write-enabled`. [Implementación de ARA en AWS Transform](https://aws.amazon.com/blogs/migration-and-modernization/new-in-aws-transform-analyze-your-code-for-modernization-and-agentic-readiness/).

### Haz una primera lectura con los informes incluidos

1. Abre el [ARA inicial](evidence/mit/before/ara/booking-mit-ara-report.md).
2. Localiza **AUTH-Q6**. Lee el hallazgo sobre integridad de auditoría y el archivo que lo sustenta.
3. Vuelve a C: si el agente escribe, necesitamos reconstruir quién aprobó y qué ocurrió. Explica esa relación.
4. Revisa **AUTH-Q3**: crear una reserva no debería autorizar su cancelación. Conéctalo con B5.
5. Consulta **STATE-Q1** y **API-Q4**: relaciona compensación e idempotencia con el dolor de A1/A4.

| Pregunta que deja el tablero | Dónde buscar evidencia |
| --- | --- |
| ¿Qué puede invocar el agente y cómo entiende el resultado? | Contrato y errores de la API |
| ¿Actúa sobre reservas propias y con el permiso de esa acción? | Identidad, scopes y aislamiento por sujeto |
| ¿La aprobación tiene efecto sobre la ejecución? | Validación del servidor y pruebas de rechazo |
| ¿Un reintento duplica el cobro? | Clave, estado durable, compensación y pruebas de recuperación |
| ¿Podemos reconstruir lo ocurrido? | Registro de operaciones y auditoría verificable |

El informe del ejemplo tiene 43 preguntas distribuidas en su propia rúbrica. Las versiones del evaluador pueden cambiar; revisa su metadata y cobertura. Conserva las etiquetas nativas: `BLOCKER`, `RISK-SAFETY` y `RISK-QUALITY` tienen significados distintos.

**Resultado de este paso:** un requisito del proceso conectado con un hallazgo, su evidencia y una prueba de aceptación. La puntuación del coach mide la facilitación; ARA aporta una evaluación técnica de la aplicación.

### Genera tu propio análisis cuando estés listo

Después de completar el coach, desde la raíz del repo:

```bash
python3 scripts/workshop.py prepare \
  --discovery .local/discovery-01 --output .local/workshop-01
```

Se generan la ficha, entregables de AI-DLC, contextos con la síntesis de tu sesión y dos clones del mismo commit para analizar. Elige otro nombre si ese destino existe. El preparador lee archivos registrados en Git: guarda los cambios en un commit antes de preparar otra versión.

Continúa en [Ejecución AWS](EJECUCION_AWS.md) para obtener ARA/MODA nuevos en tu cuenta. Los pasos siguientes también se pueden practicar con los informes públicos.

## 5. Relaciona MODA con el trabajo que necesita el agente (E–G)

Abre el [MODA de referencia](evidence/mit/after/moda/booking-mit-mod-report.md). MODA estudia la modernización y operación de la aplicación; el contexto del workflow ayuda a priorizar sus recomendaciones.

1. Localiza **DATA-Q1**: el ledger necesita conservación durable fuera del host. Relaciónalo con la auditoría que pide C.
2. Localiza **INF-Q2**: estudia qué exige operar la persistencia y recuperarla. Relaciónalo con A4.
3. Describe una mejora concreta, su dependencia y cómo probarías su efecto.
4. Usa la [plantilla de decisión](workshop/templates/decision.md): requisito → hallazgo → cambio → prueba → responsable.

### Cómo leer sus puntuaciones

MODA puntúa cada pregunta aplicable de 1 a 4 y agrupa resultados en infraestructura/plataforma, arquitectura, datos, seguridad y operación. El promedio global da igual peso a cada categoría evaluada. Revisa qué preguntas quedaron fuera antes de comparar dos promedios.

Una ruta de modernización conecta brechas con alternativas. Comprueba sus condiciones y dependencias: una recomendación de contenedores, microservicios o una base administrada requiere justificar su aporte al caso. Las preferencias tecnológicas orientan la recomendación; no cambian la puntuación de la evidencia.

Para este workshop, F es un inventario mínimo de un servicio con API, pagos, worker y auditoría. Puedes ampliar el portafolio después de completar el primer caso.

## 6. Ejecuta el agente y comprueba el flujo (H)

Ahora sí necesitas **Docker operativo**. Desde la raíz del repo:

```bash
python3 booking_lab/run.py demo --output .local/demo.json
```

Espera `DEMO_READY`. Abre una segunda terminal y sigue [la demo del agente](AGENTE_EJECUTABLE.md): prepara una reserva, rechaza una propuesta, aprueba otra, consulta el resultado y cancela con una aprobación nueva.

**Relaciona la ejecución con C:** identifica la propuesta, el paso humano, la llamada de escritura y la recuperación. Puedes repetir con lenguaje natural usando la opción Bedrock de esa misma guía.

Para comprobar automáticamente el flujo con PostgreSQL:

```bash
python3 -m unittest discover -s tests -v
python3 booking_lab/run.py e2e --output .local/db-e2e.json
```

Espera `result: passed` y `test_containers_running: 0` en el JSON. El runner comprueba aprobación, creación, consulta, cancelación, reintentos, recuperación, auditoría y restauración. Usa un archivo de salida nuevo para cada ejecución. Las instrucciones de cierre de la demo están en su guía.

## 7. Compara y lleva el aprendizaje a AI-DLC (I–J)

Abre el [ARA posterior](evidence/mit/after/ara/booking-mit-ara-report.md) y la [comparación por pregunta](evidence/mit/comparison/ara/comparison.csv).

- **AUTH-Q6:** bloqueador → `pass`; revisa la implementación del ledger y sus pruebas.
- **AUTH-Q3:** riesgo de seguridad → `pass`; revisa los permisos separados para cancelar.
- **STATE-Q1:** ya pasaba antes; no lo cuentes como una corrección de esta comparación.

Estos informes identifican sus commits de referencia. El agente y sus controles posteriores tienen sus propias [pruebas](AUDITORIA_E2E.md). Para comparar cambios tuyos, repite ARA/MODA sobre el nuevo commit conservando la misma sesión de discovery, los contextos y el alcance; sigue los comandos de [reevaluación](EJECUCION_AWS.md#6-ij-vuelve-a-medir-y-publica-evidencia).

Cierra con tres entregas a [AI-DLC](AI_DLC.md):

| Fase | Qué entregas desde el workshop |
| --- | --- |
| Inception | Dolor, alternativa, hipótesis de valor, autonomía y requisitos del flujo |
| Construction | Una unidad de trabajo, cambios revisados y pruebas de aceptación |
| Operations | Runbook, recuperación, responsable y medición con usuarios |

**Pregunta final al equipo:** ¿el resultado redujo el trabajo humano y mantuvo los controles acordados? Producto compara con la línea base y decide continuar, ajustar o detener.

## Facilitarlo con tu propio equipo

Puedes recorrerlo individualmente o compartir pantalla: una persona facilita, otra interpreta al cliente y otra conversa como coach. Lee cada situación antes de elegir y justifica la ubicación del post-it. El contenido está en [discovery.json](workshop/discovery.json); el motor y los tableros son código original MIT. Para un caso nuevo adapta preguntas, respuestas, posiciones, escenario y contextos de análisis juntos.

Puedes consultar la [conversación resuelta](examples/discovery/conversacion.md) y descargar los [tres tableros completos](examples/discovery/tableros.html) como apoyo de facilitación.

Consulta [Recursos](RECURSOS.md) para los materiales y las fuentes de la metodología.
