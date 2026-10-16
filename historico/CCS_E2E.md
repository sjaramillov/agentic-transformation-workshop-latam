> **Archivo histórico del 16 de octubre de 2026.** Describe otra implementación. El workshop público vigente comienza en [Inicio rápido](../INICIO_RAPIDO.md).

# Evaluación en una cuenta propia (CCS)

**Continuación:** las dos brechas se implementaron y validaron en la [réplica original MIT con PostgreSQL](../CCS_DATABASE_E2E.md). Este documento conserva los informes del PHP anterior y sus resultados históricos.

Fecha: **16 de octubre de 2026, UTC**. Se utilizó la sesión de CCS que el propietario abrió en su navegador. Los identificadores de cuenta, logs crudos y resultados detallados permanecen privados.

**Resultado:** se ejecutó el ciclo de análisis, dos remediaciones y nueva medición en CCS. Se corrigieron fallos de reproducción y de empaquetado. El servicio resultante **no queda aprobado para un piloto ni para producción**: ARA mantiene dos bloqueadores y las pruebas de negocio/despliegue están pendientes.

## Alcance y trazabilidad

- CloudShell `us-east-1`, Node 22.23.3, ATX 3.19.0, Python 3.13.15.
- Guía de partida: `fb681911bfc7b1ccb181d9df9a38a3bcfb3e4945`.
- Captura de entrada: SHA-256 `adb4440ce3a709a2b4f6718beb1115bf56f443c82b4cce8200b7d867b47271ce`.
- Fuente nueva y aislada: **un solo booking-service**, desde `2ef490d9a411a5f0edd1b497553dcb3def5dd580`.
- A–C ejecutados offline: ocho salidas nuevas, candidato Rebooking y autonomía P.
- Contexto ARA: SHA-256 `44c0f8cfa06ff4d64e55a8340eb3ff15cb400d597ea79b26bdc6d4ce9b2ffb2a`.
- Contexto MODA: SHA-256 `2ae53b9bd0b768a203e30c67ed5f2e7c9aebebf18cc3bbbca76d0d47f061e180`.
- Alcance ARA: `write-enabled`; MODA: preferir EKS, evitar MySQL autogestionado, despliegue manual y monolito en el lugar.

La restauración original quedó intacta. Las ramas y cambios se aplicaron solo a la copia de evaluación. Integrar un candidato en el `main` de esa copia permite volver a analizarlo; no representa aceptación para producción.

La entrada posterior quedó fijada en `f4073fc538d8aa50128fc276f3ace2b051884b60`. Para esa medición, MODA utiliza una segunda copia de booking-service y una fuente local distinta. Antes de registrarla se comprobó que su HEAD coincide exactamente con el commit de entrada del nuevo ARA. El contexto y las opciones permanecen iguales a los de sus baselines. Esto separa las escrituras de informes entre análisis; no amplía el alcance a otros servicios. El estado posterior incluye ambas TD y las correcciones originales de empaquetado y cierre de conexión, por lo que el cambio de clasificación no se atribuye exclusivamente a las TD.

## Resultados observados

| Paso | Evidencia |
| --- | --- |
| Preparación | Identidad verificada en privado; ATX saludable y acceso a catálogo |
| A–C y réplica base | 15 pruebas aprobadas, cero omitidas en CloudShell con el archivo real |
| D, ARA inicial | `complete`; 37 hallazgos: 5 BLOCKER, 12 RISK-SAFETY, 15 RISK-QUALITY, 5 INFO; tier `Not Agent-Integrable` |
| E, MODA inicial | `complete`; 7 High, 25 Medium, 2 Low; score 1.59; tier `Remediation Required`; consistencia declarada `consistent` |
| Publicación de TD | Dos nombres únicos, categoría remediation, versiones guardadas |
| H, contenedores | `completed`; seis archivos generados; build y sintaxis PHP correctos; pruebas HTTP detectaron tres fallos |
| H, bloqueadores | `completed`; PHP pasó lint externo; el probe de cierre de conexión falló y pasó después de una corrección original |
| I, ARA posterior | `complete`; 35 hallazgos: 2 BLOCKER, 12 RISK-SAFETY, 14 RISK-QUALITY, 7 INFO; tier `Remediation Required` |
| I, MODA posterior | `complete`; 4 High, 21 Medium, 10 Low; score 1.95; tier `Remediation Required`; consistencia declarada `consistent` |
| Corrección original del empaquetado | Build corregido y sondas 200/503; ruta Git bloqueada con 403; detalles en [RUNTIME_LOCAL.md](RUNTIME_LOCAL.md) |

Los informes iniciales tienen cuatro artefactos por análisis (JSON, Markdown, HTML y metadata). El nuevo [verificador](../scripts/verify_reports.py) confirmó presencia, hashes, conteos y cobertura ARA de 43 preguntas (37 hallazgos + 6 evaluaciones). ARA creó una rama y commit de informes; MODA dejó archivos sin seguimiento en `main`. Ambos conjuntos se preservaron antes de continuar, evitando arrastrar informes a la entrada de la remediación.

```bash
python3 scripts/verify_reports.py /ruta/booking-service-ara-report.json \
  --kind ara --expect-questions 43
python3 scripts/verify_reports.py /ruta/booking-service-mod-report.json --kind mod
```

El verificador comprueba estructura y conteos, no vuelve a juzgar la rúbrica ni certifica el runtime. Las sesiones de análisis indicaron `NO_EXIT_CRITERIA_DEFINED` cuando la definición no incluía criterios de salida; se conserva esa limitación junto a la comprobación externa de sus artefactos.

## Comparación ARA

Los bloqueadores iniciales fueron `API-Q4`, `AUTH-Q1`, `AUTH-Q6`, `STATE-Q1` y `DATA-Q1`. El informe posterior conserva **AUTH-Q6 (auditoría atribuible y durable)** y **STATE-Q1 (compensación después de cobrar)**. La TD no alcanzó su objetivo declarado de cero bloqueadores. Las limitaciones independientes de scopes, privacidad e idempotencia siguen requiriendo pruebas aunque el analizador cambie su categoría.

## Comparación MODA

Los hallazgos altos bajaron de **7 a 4** y el score pasó de **1.59 a 1.95**. La clasificación se mantuvo en **Remediation Required**. Los hallazgos totales pasaron de 34 a 35 (7/25/2 → 4/21/10 por severidad); reducir los altos no implica que todos los totales deban bajar ni que el servicio esté listo. Ambos conjuntos posteriores pasaron la verificación independiente de archivos y conteos.

## Fallos encontrados durante la ejecución

1. **Sonda falsa positiva:** PHP devolvió HTTP 200 con un error fatal por DB ausente; Docker mostraba `healthy`.
2. **Enrutamiento ausente:** `/api/bookings` devolvía 404 de Apache.
3. **Exposición del repositorio:** `/.git/config` devolvía 200 porque el Dockerfile copiaba todo el árbol bajo el directorio servido.
4. **Espacio insuficiente:** una segunda construcción agotó el volumen raíz de CloudShell. Se recuperó espacio con limpieza de objetos propios identificados y se volvió a construir.
5. **Idempotencia defectuosa:** la segunda TD persistía la respuesta desde un callback con una conexión ya cerrada. Una prueba con `mysqli` simulado reprodujo el error; retirar ese cierre prematuro hizo pasar la regresión.
6. **IaC incompleta:** cfn-lint encontró errores en las plantillas de plataforma. Los detalles y límites de las TD están en [LIMITACIONES_TD.md](LIMITACIONES_TD.md).

## Límites de la evidencia

- La ampliación opcional F a tres servicios y el rollup de cartera no están validados. El estado final de un análisis CT no acredita por sí solo sus rollups.
- No se creó un clúster EKS, una base RDS ni un despliegue de TravelCorp.
- Las comprobaciones HTTP se hicieron sin DB. Falta el recorrido de reservas con datos sintéticos, pagos controlados, reintentos, fallos y concurrencia.
- No se ha demostrado autenticación desplegada, aislamiento del origen, auditoría de negocio durable, residencia efectiva ni aprobación humana.
- El costo de AWS Transform depende de minutos de agente; no se ha verificado un límite duro propagado por CT. Los contadores del agente no sustituyen la factura.

La evidencia agregada está en [evidence/ccs-audit.json](../evidence/ccs-audit.json). No debe interpretarse la clasificación de un informe como aprobación de despliegue.

## Priorización de las brechas observadas (G)

| Prioridad | Trabajo concreto | Evidencia necesaria para cerrar |
| --- | --- | --- |
| 1 | Atribuir cada escritura a una identidad M2M validada y entregar eventos de negocio a almacenamiento durable | Petición, principal, correlación y evento consultable; prueba de entrega fallida y acceso restringido |
| 1 | Compensar fallos después del cobro y antes de persistir la reserva | Doble de pagos, fallo forzado de INSERT, recuperación y ausencia de cobros/reservas huérfanos |
| 1 | Completar la frontera de autenticación y autorización | Stage, scopes, origen privado o control equivalente; token ausente, expirado y con scope incorrecto rechazados |
| 1 | Completar idempotencia y concurrencia | Clave delimitada por identidad/operación, huella del cuerpo, dos réplicas, fallo entre efecto y registro, replay y recuperación |
| 2 | Completar infraestructura, secretos y pipeline | cfn-lint sin errores, configuración regional comprobada, artefactos reales de source/build/deploy y rollback probado |

Los responsables concretos deben asignarse en el equipo: aplicación, plataforma e identidad. No se inventan personas ni aprobaciones organizacionales.

La suite pública ampliada pasó **24 pruebas, cero omitidas**, en Python 3.14.0 con la captura real. Este conteo corresponde a las herramientas de reproducción, no a 24 pruebas del negocio TravelCorp.

El clon limpio del commit `9628624` también pasó las 24 pruebas y quedó sin cambios. [CI aprobó las cuatro combinaciones Linux/macOS × Python 3.11/3.14](https://github.com/sjaramillov/agentic-transformation-workshop-latam/actions/runs/38844539617); la prueba del archivo privado se omite en CI.

### Detalle de cobertura y trazabilidad del cierre

El ARA posterior enumera las 43 preguntas: **35 hallazgos, 7 evaluaciones `pass` y 1 `not_evaluated_extended` (`API-Q6`)**. Son 42 preguntas evaluadas; el validador comprueba que las 43 estén contabilizadas, no que todas hayan sido evaluadas. La media de las cinco puntuaciones de categoría MODA es 1.954, compatible con el 1.95 publicado.

El metadata de MODA no identifica una versión exacta de la TD administrada por AWS y marca `has_deployed_workload: true` a partir de los archivos analizados. **Ese flag no es evidencia de un despliegue ejecutado.** Se conservan estas limitaciones; no se garantiza que una ejecución futura del servicio administrado produzca los mismos juicios. El intento de exportar ambas definiciones con `atx custom def get -n AWS/... --td <directorio-existente> --json` fue rechazado con `ValidationException: Unauthorized operation on package with reserved prefix: AWS/`. No se obtuvo una copia ni una versión verificable de esas TD administradas.

Al cerrar no quedaron análisis en estado `running` ni contenedores de prueba. Se retiraron las imágenes propias y registros de caché identificados; CloudShell quedó con 3.2 GiB libres en el volumen raíz. El respaldo completo de código, Git, contextos e informes se descargó y verificó por SHA-256, y permanece privado.

Las seis sesiones principales reportaron **238.5175 minutos de agente**. A [USD 0.035 por minuto](https://aws.amazon.com/transform/pricing/) equivalen nominalmente a **USD 8.35**; es una estimación a partir de esos contadores, no una lectura de la factura ni de descuentos/redondeos.
