# Cómo aceptar una transformación

La TD original [hardening](workshop/transformations/hardening/transformation_definition.md) está incluida bajo MIT. Sus instrucciones son editables y pueden publicarse en tu cuenta Transform. El criterio de éxito es una corrección demostrada.

## Lista de revisión

1. Relaciona cada cambio con un `question_id` y evidencia del informe.
2. Reproduce el fallo o prueba que el hallazgo no aplica al código evaluado.
3. Comprueba autorización, replay y aislamiento entre sujetos con pruebas negativas.
4. Comprueba que la recuperación conserve el estado y las claves de idempotencia.
5. Ejecuta el E2E con PostgreSQL y conserva el resultado, commit y hashes.
6. Repite ARA/MODA con el mismo contexto. Conserva también las observaciones que continúan abiertas.

No aceptes como prueba de despliegue un Dockerfile, una plantilla o una ejecución de análisis. Tampoco aceptes una corrección que elimine preguntas de la rúbrica o cambie el alcance a solo lectura para ocultar un fallo de escritura.

Los detalles de las transformaciones antiguas se conservan en [el archivo histórico](historico/LIMITACIONES_TD.md). Las correcciones actuales se documentan en [CCS_E2E.md](CCS_E2E.md).
