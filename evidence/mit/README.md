# Evidencia pública de Booking MIT — CCS

Esta carpeta permite revisar los resultados sin acceder a la cuenta CCS. [Conclusiones y revisión por pregunta](../../CCS_E2E.md).

| Medición | JSON | Markdown | HTML | Procedencia / validación |
| --- | --- | --- | --- | --- |
| ARA antes | [JSON](before/ara/booking-mit-ara-report.json) | [MD](before/ara/booking-mit-ara-report.md) | [HTML](before/ara/booking-mit-ara-report.html) | [Hashes](before/ara-provenance.json) |
| ARA después | [JSON](after/ara/booking-mit-ara-report.json) | [MD](after/ara/booking-mit-ara-report.md) | [HTML](after/ara/booking-mit-ara-report.html) | [Hashes](after/ara-provenance.json), [verificación](after/ara-verification.json) |
| MODA después | [JSON](after/moda/booking-mit-mod-report.json) | [MD](after/moda/booking-mit-mod-report.md) | [HTML](after/moda/booking-mit-mod-report.html) | [Hashes](after/moda-provenance.json), [verificación](after/moda-verification.json) |

La metadata original acompaña cada informe. La sanitización sustituye únicamente el directorio del usuario de CloudShell por `${HOME}`; la procedencia conserva hashes del archivo crudo y publicado. No se cambian los hallazgos ni las puntuaciones.

- [Comparación ARA JSON](comparison/ara/comparison.json) y [CSV](comparison/ara/comparison.csv): 43 preguntas, dos cierres por código y dos variaciones en preguntas extendidas.
- [Fuente y contexto](provenance.json), [hashes de fuente](source-sha256.json), [hashes de contexto](context-sha256.json).
- [E2E CCS aprobado](runtime/final-db-e2e-02.json) y [fallo anterior por falta de espacio](runtime/final-db-e2e.json).
- [E2E GitHub Actions](runtime/github-actions-db-e2e.json).
- [Verificación de demo manual](runtime/manual-demo-verification.json), [crear](runtime/final-demo-create.json), [listar](runtime/final-demo-list.json), [otro sujeto](runtime/final-demo-other-subject.json), [cancelar](runtime/final-demo-cancel.json), [repetir creación](runtime/final-demo-create-replay.json), [repetir cancelación](runtime/final-demo-cancel-replay.json), [cierre](runtime/final-demo.json).
- [Registro de TD original](runtime/td-publish-03.json).

Los secretos generados en cada ejecución no son parte del código ni de las pruebas publicadas. Cada clon crea sus propias credenciales automáticamente. Los informes completos y los recibos funcionales están aquí; no se requiere un paquete privado.
