# Verificación del workshop público

**Versión actual comprobada:** [112 pruebas, 28/28 escenarios E2E deterministas en dos ejecuciones y 7/7 casos con Bedrock real en CCS](evidence/bedrock/README.md). Cada capa conserva su fuente, fecha y alcance; la [evidencia determinista anterior](evidence/agent-workshop/README.md) sigue disponible.

La aceptación del recorrido ampliado distingue estas capas:

| Capa | Cómo reproducir | Evidencia |
| --- | --- | --- |
| Materiales y herramientas | `python3 -m unittest discover -s tests -v` | CI pública, enlaces y preparación desde Git |
| Agente y contrato con PostgreSQL | `python3 booking_lab/run.py e2e --output .local/db-e2e.json` | JSON y artefactos `database-e2e-evidence-1` y `database-e2e-evidence-2` de cada ejecución de CI; referencia anterior en [CCS_DATABASE_E2E.md](CCS_DATABASE_E2E.md) |
| Agente con Bedrock real y PostgreSQL | `python3 booking_lab/bedrock_e2e.py --live-bedrock --confirm-test-operator --model-id amazon.nova-micro-v1:0 --region us-east-1 --output .local/bedrock-live-01.json` | [Recibos en CCS](evidence/bedrock/README.md): cuatro inferencias, siete casos, fallo inicial y corrección |
| Evaluación de AWS Transform | [Ejecución AWS](EJECUCION_AWS.md) | [CCS_E2E.md](CCS_E2E.md), informes históricos del 16 de octubre con sus commits |
| Hipótesis de negocio | [Ficha de valor](FICHA_VALOR.md) y [AI-DLC](AI_DLC.md) | Línea base y resultado medidos por cada equipo; el caso incluido es ilustrativo |

La suite pública usa materiales presentes en Git y no requiere una captura de evento. La prueba opcional de una captura histórica se conserva separada en `historico/`.

## Aceptación del agente ejecutable

La suite de base de datos incluye los 18 casos originales y diez casos adicionales: una prueba de aprobación en servidor y nueve recorridos de la CLI real. El conjunto comprueba:

- Capacidad ausente, vencida, firmada con otra clave o vinculada a otro sujeto/cuerpo/operación: 403 sin intención ni cobro.
- Planificar y rechazar antes de ejecutar: ninguna escritura.
- Crear, observar y repetir el mismo estado: un solo cobro.
- Dos procesos CLI sobre el mismo archivo: un intento persistido y un cobro.
- Alterar una propuesta aprobada: rechazo antes de llamar a herramientas.
- Consultar con sujetos distintos: aislamiento de reservas.
- Recuperar caída del proveedor con el mismo plan y clave.
- Retirar aprobación después del envío: conservar la posibilidad de reconciliar una operación remota que puede continuar.
- Reiniciar la API después de un cobro confirmado por el proveedor: recuperar sin volver a cobrar.
- Cancelar con aprobación nueva y repetir: un reembolso.

El resultado aceptable tiene `result: passed`, todos los casos aprobados, cinco invariantes en cero y cierre comprobado (`cleanup.result: passed`, `cleanup.unknown_count: 0` y `test_containers_running: 0`). Un error al detener o inspeccionar recursos hace fallar el runner y conserva la evidencia. `source_sha256` vincula el recibo al código y `repository_commit` registra la revisión. La CI ejecuta la suite unitaria en Linux/macOS con Python 3.11/3.14 y dos repeticiones independientes del E2E de DB en Linux. La barrera `snapshot_barrier` debe estar aprobada, con los escritores detenidos y las colas vacías antes del backup.

La suite habitual comprueba `rules`: las llamadas HTTP, la persistencia y las fallas son reales en el entorno sintético. Las pruebas unitarias de Bedrock usan respuestas controladas. Además, el runner independiente `bedrock_e2e.py` pasó con **Amazon Nova Micro real en CCS**: tres planes exactos y un rechazo semántico esperado, sin fallback a reglas. Sus [recibos](evidence/bedrock/README.md) incluyen DB, restauración y recuperación sin otra inferencia. Esta prueba acotada no mide calidad general del modelo. Escribir requiere aprobación; el E2E usa un aprobador automatizado limitado a sus fixtures sintéticos.

La revisión adversarial añadió regresiones para proxies y redirecciones, respuestas con otra reserva, aprobación vencida en tránsito y retiro después del envío. El E2E registra confirmaciones explícitas de un operador de prueba; no acredita identidad humana independiente del emisor local.

## Trazabilidad

El preparador [workshop.py](scripts/workshop.py) extrae archivos de un commit Git concreto y registra SHA256. ARA y MODA usan clones separados del mismo contenido. Las pruebas de DB registran las imágenes y hashes del código ejecutado. La comparación debe enlazar esos identificadores para distinguir fuente, evaluación y runtime.

## Revisar antes de publicar

Los resultados funcionales sanitizados se pueden publicar; los archivos `.env`, tokens, cuentas y logs crudos se revisan por separado. El código, contexto y ejercicios originales completos siguen disponibles bajo MIT.

La auditoría de la implementación anterior está en [Histórico](historico/AUDITORIA_E2E.md).
