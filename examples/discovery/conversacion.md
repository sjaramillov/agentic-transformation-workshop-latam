> Ejemplo resuelto: preguntas recomendadas del caso educativo.

# Discovery de Booking MIT

Práctica guiada con cliente y coach. Las cifras son supuestos del caso.

Situaciones respondidas: 21/21.

La puntuación describe elecciones de facilitación. La evaluación de código se realiza con ARA/MODA.

## A. Entender el proceso

Preguntas recomendadas elegidas: 9/9.

### Escucha un caso real

**Pregunta elegida:** Cuéntame la última vez que ocurrió: ¿qué intentaban hacer y dónde se atascaron?

**Cliente:** Ayer intentamos confirmar una reserva. La pantalla no respondió y no sabíamos si el cobro había ocurrido. Tuvimos que consultar y conciliar antes de intentar otra vez.

**Coach:** Un episodio concreto permite descubrir trabajo, incertidumbre y consecuencias. Primero sigue el dolor del cliente; después podrás valorar una solución.

**Síntesis para el tablero:** Ayer intentamos confirmar una reserva. La pantalla no respondió y no sabíamos si el cobro había ocurrido. Tuvimos que consultar y conciliar antes de intentar otra vez.

### Delimita el proceso

**Pregunta elegida:** ¿Con qué solicitud comienza el caso y qué debe haber ocurrido para darlo por terminado?

**Cliente:** Empezamos con una solicitud de reserva. Cerramos cuando sabemos que está confirmada o que el fallo quedó resuelto, incluido el reembolso si hubo un cobro. Una respuesta HTTP no basta.

**Coach:** Acordar inicio y final evita optimizar un paso dejando la conciliación fuera del proceso.

**Síntesis para el tablero:** Empezamos con una solicitud de reserva. Cerramos cuando sabemos que está confirmada o que el fallo quedó resuelto, incluido el reembolso si hubo un cobro. Una respuesta HTTP no basta.

### Recorre el caso habitual

**Pregunta elegida:** Cuando todo sale bien, ¿qué sucede entre la solicitud y la confirmación?

**Cliente:** Recogemos itinerario e importe, mostramos la propuesta, la persona confirma, se captura el pago y se registra la reserva. Después podemos consultar su estado.

**Coach:** Ordenar los eventos te permite colocar cada dolor en un punto del proceso. La descomposición técnica vendrá después.

**Síntesis para el tablero:** Recogemos itinerario e importe, mostramos la propuesta, la persona confirma, se captura el pago y se registra la reserva. Después podemos consultar su estado.

### Sigue la excepción

**Pregunta elegida:** ¿Cómo distinguen esos dos casos y qué debe ocurrir con el dinero en cada uno?

**Cliente:** Si no sabemos el resultado, consultamos la operación y repetimos la misma solicitud sin duplicarla. Si sabemos que la reserva falló tras cobrar, necesitamos un reembolso que pueda retomarse aunque pagos esté caído.

**Coach:** Separar incertidumbre de fallo confirmado revela dos requisitos: reintento sin efectos duplicados y compensación recuperable.

**Síntesis para el tablero:** Si no sabemos el resultado, consultamos la operación y repetimos la misma solicitud sin duplicarla. Si sabemos que la reserva falló tras cobrar, necesitamos un reembolso que pueda retomarse aunque pagos esté caído.

### Identifica a las personas

**Pregunta elegida:** ¿Quién solicita, quién aprueba y quién se encarga de resolver una operación pendiente?

**Cliente:** El viajero solicita y confirma su operación. El operador ayuda a revisar el estado y conciliar excepciones. Producto acepta el alcance; ingeniería implementa y operaciones se encarga de recuperar el servicio.

**Coach:** Los actores y sus responsabilidades permiten definir límites de acceso y evitar que una excepción quede sin dueño.

**Síntesis para el tablero:** El viajero solicita y confirma su operación. El operador ayuda a revisar el estado y conciliar excepciones. Producto acepta el alcance; ingeniería implementa y operaciones se encarga de recuperar el servicio.

### Distingue reglas y criterio

**Pregunta elegida:** ¿Qué decisiones siguen una regla y cuáles necesitan interpretar la intención o aclarar una excepción?

**Cliente:** Validar un importe o repetir la misma operación puede seguir reglas. Entender lo que pide una persona y explicar un estado ambiguo puede necesitar interpretación. Los casos comerciales excepcionales requieren más contexto y revisión.

**Coach:** Busca el punto donde hace falta criterio. Un proceso puede combinar reglas, asistencia y decisiones humanas.

**Síntesis para el tablero:** Validar un importe o repetir la misma operación puede seguir reglas. Entender lo que pide una persona y explicar un estado ambiguo puede necesitar interpretación. Los casos comerciales excepcionales requieren más contexto y revisión.

### Pregunta por la información

**Pregunta elegida:** ¿Qué información usan para decidir y cuál pueden consultar mediante una API hoy?

**Cliente:** El laboratorio permite consultar reservas por API y retomar la operación desde el estado guardado del agente. La propuesta recibe itinerario e importe. Las excepciones comerciales que estamos imaginando necesitarían información adicional del cliente, hoy fuera del alcance del laboratorio.

**Coach:** Relaciona cada decisión con sus datos. Registra como pendiente aquello que todavía no es accesible.

**Síntesis para el tablero:** El laboratorio permite consultar reservas por API y retomar la operación desde el estado guardado del agente. La propuesta recibe itinerario e importe. Las excepciones comerciales que estamos imaginando necesitarían información adicional del cliente, hoy fuera del alcance del laboratorio.

### Prioriza los dolores

**Pregunta elegida:** ¿Qué les consume más trabajo y qué error tendría una consecuencia inaceptable?

**Cliente:** Queremos reducir consultas y conciliaciones repetidas. Un cobro duplicado, una escritura sin aprobación o acceder a la reserva de otra persona detendrían el piloto. El tiempo ahorrado debe incluir la revisión y recuperación.

**Coach:** Combina beneficio esperado con condiciones de parada. La demostración debe responder al trabajo que el cliente quiere mejorar.

**Síntesis para el tablero:** Queremos reducir consultas y conciliaciones repetidas. Un cobro duplicado, una escritura sin aprobación o acceder a la reserva de otra persona detendrían el piloto. El tiempo ahorrado debe incluir la revisión y recuperación.

### Marca las dependencias

**Pregunta elegida:** ¿Qué servicios o equipos necesitamos y qué ocurre si no están disponibles?

**Cliente:** La API y PostgreSQL conservan las operaciones. El proveedor de pagos del laboratorio es simulado, pero puede fallar. El worker retoma trabajo pendiente. Para operar con usuarios reales tendremos que acordar despliegue, secretos, copias y monitorización.

**Coach:** Las dependencias y sus fallos conectan el proceso con requisitos técnicos concretos. El tablero A ya expresa qué debe poder recuperarse.

**Síntesis para el tablero:** La API y PostgreSQL conservan las operaciones. El proveedor de pagos del laboratorio es simulado, pero puede fallar. El worker retoma trabajo pendiente. Para operar con usuarios reales tendremos que acordar despliegue, secretos, copias y monitorización.

## B. Elegir la oportunidad

Preguntas recomendadas elegidas: 6/6.

### Elige dónde hace falta ayuda

**Pregunta elegida:** ¿Qué parte resolveríamos con reglas y dónde ayudaría interpretar y explicar una intención?

**Cliente:** Conservaríamos reglas para cobros, permisos y recuperación. Exploraríamos un asistente que prepare la operación, explique su estado y pida confirmación antes de escribir.

**Coach:** La oportunidad está en una tarea delimitada. Los controles deterministas siguen siendo parte de la solución.

**Síntesis para el tablero:** Conservaríamos reglas para cobros, permisos y recuperación. Exploraríamos un asistente que prepare la operación, explique su estado y pida confirmación antes de escribir.

### Comprueba si los datos alcanzan

**Pregunta elegida:** ¿Cuál puede trabajar con los datos accesibles y cuál necesita integrar nuevas fuentes?

**Cliente:** Podemos practicar reservas y consulta de estado con las API actuales. Las excepciones comerciales necesitan fuentes y permisos adicionales. Esa oportunidad empieza con trabajo de datos.

**Coach:** Cruzar necesidad de criterio con disponibilidad de datos diferencia una oportunidad practicable de otra que requiere preparación.

**Síntesis para el tablero:** Podemos practicar reservas y consulta de estado con las API actuales. Las excepciones comerciales necesitan fuentes y permisos adicionales. Esa oportunidad empieza con trabajo de datos.

### Compara alternativas

**Pregunta elegida:** ¿Cómo compararíamos un formulario, un asistente de consulta y un agente con aprobación?

**Cliente:** El formulario podría bastar para capturar una reserva. Un asistente de consulta ayuda a interpretar su estado. Un agente con aprobación también prepara y ejecuta la operación. Compararemos tiempo total, errores, revisión y costo.

**Coach:** Una oportunidad se justifica frente a alternativas. La ficha de valor debe permitir preferir la opción más sencilla si resuelve el problema. En el tablero las candidatas salen de la bandeja y ocupan su cuadrante.

**Síntesis para el tablero:** El formulario podría bastar para capturar una reserva. Un asistente de consulta ayuda a interpretar su estado. Un agente con aprobación también prepara y ejecuta la operación. Compararemos tiempo total, errores, revisión y costo. Ubicamos las alternativas en el cuadrante usando criterio requerido y acceso a datos.

### Acordar cómo medir

**Pregunta elegida:** ¿Cuál es la línea base, qué objetivo probaríamos y qué cifras siguen siendo supuestos?

**Cliente:** Para practicar usamos 200 casos al mes, 8 minutos humanos por caso y una meta de 6. Son supuestos. Mediremos revisión, errores y recuperación; el resultado técnico no mide por sí mismo ese ahorro.

**Coach:** Explicita la unidad y la procedencia. Una hipótesis medible enlaza la construcción con el valor que producto quiere comprobar.

**Síntesis para el tablero:** Para practicar usamos 200 casos al mes, 8 minutos humanos por caso y una meta de 6. Son supuestos. Mediremos revisión, errores y recuperación; el resultado técnico no mide por sí mismo ese ahorro.

### Conserva la aprobación

**Pregunta elegida:** ¿Qué debe aprobar una persona y qué permisos necesita cada acción?

**Cliente:** Consultar reservas propias no necesita una aprobación de escritura. Crear requiere revisar itinerario e importe. Cancelar exige una aprobación nueva para esa reserva. La identidad y el permiso deben corresponder a cada acción.

**Coach:** La aprobación tiene alcance concreto. ARA deberá revisar identidad, permisos por acción y controles de supervisión humana.

**Síntesis para el tablero:** Consultar reservas propias no necesita una aprobación de escritura. Crear requiere revisar itinerario e importe. Cancelar exige una aprobación nueva para esa reserva. La identidad y el permiso deben corresponder a cada acción.

### Fija un alcance inicial

**Pregunta elegida:** ¿Empezamos proponiendo y esperando confirmación, con qué límites y condiciones de parada?

**Cliente:** El alcance inicial es preparar y confirmar: crear, consultar y cancelar reservas propias con pagos sintéticos. Una escritura sin aprobación, un duplicado o un acceso cruzado detienen el ejercicio.

**Coach:** El nivel de autonomía deriva del riesgo y del acuerdo con el cliente. Esta práctica fija una base común para diseñar y evaluar.

**Síntesis para el tablero:** El alcance inicial es preparar y confirmar: crear, consultar y cancelar reservas propias con pagos sintéticos. Una escritura sin aprobación, un duplicado o un acceso cruzado detienen el ejercicio.

## C. Diseñar y evaluar

Preguntas recomendadas elegidas: 6/6.

### Confirma qué vas a construir

**Pregunta elegida:** ¿Qué tarea inicial conecta mejor el dolor descubierto con un resultado observable?

**Cliente:** Primero una reserva aprobada que podamos consultar y recuperar sin duplicados. Después su cancelación con otra aprobación. Así podemos observar el tiempo total y los errores del caso.

**Coach:** Una primera unidad de trabajo acotada permite validar el recorrido completo y llevarlo a Construction en AI-DLC.

**Síntesis para el tablero:** Primero una reserva aprobada que podamos consultar y recuperar sin duplicados. Después su cancelación con otra aprobación. Así podemos observar el tiempo total y los errores del caso.

### Define el inicio del agente

**Pregunta elegida:** ¿Qué inicia el flujo y qué datos deben estar claros antes de proponer una escritura?

**Cliente:** El usuario pide una reserva con itinerario e importe. Si falta un dato, el agente debe pedirlo o rechazar la planificación. La falta de información no autoriza una escritura.

**Coach:** Define entradas y condiciones de detención antes de llamar herramientas. El flujo empieza con intención explícita.

**Síntesis para el tablero:** El usuario pide una reserva con itinerario e importe. Si falta un dato, el agente debe pedirlo o rechazar la planificación. La falta de información no autoriza una escritura.

### Distingue consultas y acciones

**Pregunta elegida:** ¿Qué llamadas consultan información y cuáles producen efectos sobre reservas y pagos?

**Cliente:** GET /bookings y GET /bookings/{id} consultan reservas. POST /bookings crea y DELETE /bookings/{id} cancela con reembolso. El contrato exacto se revisa en booking_lab/service.py.

**Coach:** Clasificar lectura y escritura concreta la superficie de evaluación. ARA se ejecutará con alcance write-enabled para este caso.

**Síntesis para el tablero:** GET /bookings y GET /bookings/{id} consultan reservas. POST /bookings crea y DELETE /bookings/{id} cancela con reembolso. El contrato exacto se revisa en booking_lab/service.py.

### Diseña la puerta humana

**Pregunta elegida:** ¿Qué revisa la persona y cómo se vincula su aprobación a esta operación concreta?

**Cliente:** La persona revisa acción, identidad, itinerario o reserva e importe. El rechazo no produce escritura. La aprobación debe estar vinculada a esa propuesta y ser validada por la API.

**Coach:** La aprobación debe tener efecto en la ejecución. Incluye este requisito en ARA y prueba tanto aceptación como rechazo.

**Síntesis para el tablero:** La persona revisa acción, identidad, itinerario o reserva e importe. El rechazo no produce escritura. La aprobación debe estar vinculada a esa propuesta y ser validada por la API.

### Cierra la recuperación

**Pregunta elegida:** ¿Cómo retomamos la misma operación y cómo reconstruimos lo que se aprobó y ejecutó?

**Cliente:** Guardamos la intención y su clave, consultamos el estado y retomamos esa operación. Si hubo un fallo después del cobro, conciliamos o compensamos. Debe existir auditoría atribuible y verificable.

**Coach:** El diseño debe cubrir resultado incierto, compensación y evidencia. Esos requisitos llegan a ARA como idempotencia, estado y auditoría.

**Síntesis para el tablero:** Guardamos la intención y su clave, consultamos el estado y retomamos esa operación. Si hubo un fallo después del cobro, conciliamos o compensamos. Debe existir auditoría atribuible y verificable.

### Entrega el contexto a ARA y MODA

**Pregunta elegida:** ¿Qué debe comprobar ARA y qué necesidades de operación debe estudiar MODA para este alcance?

**Cliente:** ARA debe comprobar API, identidad, aprobación, reintentos, compensación y auditoría para crear, consultar y cancelar reservas propias. MODA debe estudiar despliegue, secretos, persistencia, recuperación y observación para una operación mantenible.

**Coach:** La evaluación recibe requisitos y una superficie concreta. Los informes servirán para priorizar trabajo; el coach evalúa cómo facilitaste, no certifica el código ni el beneficio.

**Síntesis para el tablero:** ARA debe comprobar API, identidad, aprobación, reintentos, compensación y auditoría para crear, consultar y cancelar reservas propias. MODA debe estudiar despliegue, secretos, persistencia, recuperación y observación para una operación mantenible.
