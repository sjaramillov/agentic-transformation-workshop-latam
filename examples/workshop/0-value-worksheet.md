# Ficha de valor — completar antes de construir

## 1. Problema y decisión

- ID de oportunidad:
- Usuario y proceso afectados:
- Problema observado y fuente (entrevista, ticket, medición, fecha):
- Frecuencia / población / periodo:
- Consecuencia de mantener el proceso actual:
- Resultado que queremos cambiar:
- Responsable de negocio y fecha de decisión:
- Decisión: investigar / experimentar / continuar / detener:

## 2. Hipótesis y medición

> Si cambiamos ___ para ___, esperamos que ___ pase de ___ a ___ durante ___, sin empeorar ___.

| Métrica | Definición / unidad | Línea base | Fuente / fecha | Objetivo | Cómo y cuándo medir | Responsable |
| --- | --- | --- | --- | --- | --- | --- |
| Resultado para el usuario | | | | | | |
| Tiempo humano total, incluida revisión y recuperación | | | | | | |
| Calidad / errores | | | | | | |
| Costo por caso completado | | | | | | |

Marcar cada valor como **observado**, **supuesto** o **por medir**. Un test técnico y una puntuación ARA/MODA no miden retorno de inversión.

## 3. Alternativas y elección

| Alternativa | Beneficio esperado | Esfuerzo / costo | Riesgo | Evidencia que falta |
| --- | --- | --- | --- | --- |
| Mantener y mejorar el procedimiento manual | | | | |
| Formulario o automatización determinista sencilla | | | | |
| Asistente de consulta, sin escritura | | | | |
| Agente que propone y ejecuta tras aprobación | | | | |

- Alternativa elegida y razón verificable:
- Qué resultado haría preferible la alternativa más sencilla:
- Fuera de alcance:

## 4. Autonomía y límites

- Acciones permitidas:
- Datos / sujetos / servicios permitidos:
- Acciones que exigen aprobación y quién puede aprobar:
- Límites por operación, sesión y periodo:
- Qué ocurre ante rechazo, timeout, respuesta ambigua o resultado contradictorio:
- Condiciones de parada y responsable de recuperación:

## 5. Esfuerzo, costo y decisión económica

- Horas de implementación y mantenimiento (supuesto / observado):
- Tiempo de validación y revisión humana por caso:
- Costo de modelo, infraestructura, observabilidad y almacenamiento; fuente / fecha / unidad:
- Costo de errores y recuperación:
- Límite del experimento y quién lo autoriza:
- Beneficio bruto estimado y fórmula:
- Beneficio neto estimado, supuestos y sensibilidad:

Registrar un campo como **por medir** cuando no haya datos. No convertir un ahorro de tiempo supuesto en ingreso realizado.

## 6. Experimento y aceptación

- Participantes / casos / ventana / tratamiento de datos:
- Comparador y asignación del orden de ejecución:
- Métricas de resultado y guardas:
- Umbral de éxito y razón de elegirlo:
- Criterio de fracaso o parada inmediata:
- Pruebas técnicas previas al experimento:
- Evidencia requerida para continuar:
- Resultado observado, fecha y decisión final:

## 7. Trazabilidad

Para cada requisito registrar: **métrica → caso de uso → autonomía → hallazgo ARA/MODA → cambio → prueba → resultado observado → siguiente medición**.

- Commit / ID de práctica:
- Ruta a la matriz de trazabilidad:
- Riesgos aceptados, responsable y fecha de revisión:
