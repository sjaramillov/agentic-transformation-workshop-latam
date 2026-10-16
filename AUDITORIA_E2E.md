# Verificación del workshop público

La aceptación tiene tres capas:

| Capa | Cómo reproducir | Evidencia |
| --- | --- | --- |
| Materiales y herramientas | `python3 -m unittest discover -s tests -v` | CI pública, enlaces y preparación desde Git |
| Contrato con PostgreSQL | `python3 booking_lab/run.py e2e --output .local/db-e2e.json` | [CCS_DATABASE_E2E.md](CCS_DATABASE_E2E.md) y JSON de cada ejecución |
| Evaluación de AWS Transform | [Ejecución AWS](EJECUCION_AWS.md) | [CCS_E2E.md](CCS_E2E.md), informes y comparación por pregunta |

La suite pública usa materiales presentes en Git y no requiere una captura de evento. La prueba opcional de una captura histórica se conserva separada en `historico/`.

## Trazabilidad

El preparador [workshop.py](scripts/workshop.py) extrae archivos de un commit Git concreto y registra SHA256. ARA y MODA usan clones separados del mismo contenido. Las pruebas de DB registran las imágenes y hashes del código ejecutado. La comparación debe enlazar esos identificadores para distinguir fuente, evaluación y runtime.

## Revisar antes de publicar

Los resultados funcionales sanitizados se pueden publicar; los archivos `.env`, tokens, cuentas y logs crudos se revisan por separado. El código, contexto y ejercicios originales completos siguen disponibles bajo MIT.

La auditoría de la implementación anterior está en [Histórico](historico/AUDITORIA_E2E.md).
