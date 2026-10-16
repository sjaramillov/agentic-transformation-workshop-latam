# Booking MIT: corregir hallazgos verificables

## Objetivo

Corregir los hallazgos ARA/MODA seleccionados en el contexto de ejecución. Trabajar exclusivamente sobre el servicio original `booking_lab/`. Conservar contrato, aislamiento por sujeto, idempotencia, saga durable y auditoría transaccional.

## Procedimiento

1. Leer el informe seleccionado y comprobar cada hallazgo contra el código. Registrar identificador, evidencia y criterio de aceptación.
2. Implementar el cambio mínimo coherente. No convertir una propuesta de infraestructura en una afirmación de despliegue. No excluir preguntas ni rebajar el alcance de agentes para mejorar la puntuación.
3. Añadir pruebas positivas, negativas y de recuperación para el comportamiento que cambia. Conservar los escenarios previos.
4. Ejecutar `python3 booking_lab/run.py e2e --output .local/remediation-e2e.json` si Docker está disponible. Si no, declarar la ejecución pendiente con causa concreta.
5. Revisar el diff y entregar resumen, pruebas, limitaciones y riesgos restantes. No publicar, desplegar recursos cloud ni modificar IAM.

## Criterios de salida

- El fallo seleccionado tiene una reproducción y una prueba que pasa tras la corrección.
- Los escenarios E2E continúan pasando y las invariantes de DB son cero.
- No hay claves, tokens, cuentas o datos privados versionados.
- El resultado identifica el commit, el informe de entrada y los archivos cambiados.
