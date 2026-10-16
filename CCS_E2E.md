# Evaluación en una cuenta propia (CCS)

Fecha: **16 de octubre de 2026, UTC**. Se utilizó la sesión de CCS que el propietario abrió en su navegador. Los identificadores de cuenta, logs crudos y resultados detallados permanecen privados.

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
| Corrección original del empaquetado | Build corregido y sondas 200/503; ruta Git bloqueada con 403; detalles en [RUNTIME_LOCAL.md](RUNTIME_LOCAL.md) |

Los informes iniciales tienen cuatro artefactos por análisis (JSON, Markdown, HTML y metadata). El nuevo [verificador](scripts/verify_reports.py) confirmó presencia, hashes, conteos y cobertura ARA de 43 preguntas (37 hallazgos + 6 evaluaciones). ARA creó una rama y commit de informes; MODA dejó archivos sin seguimiento en `main`. Ambos conjuntos se preservaron antes de continuar, evitando arrastrar informes a la entrada de la remediación.

```bash
python3 scripts/verify_reports.py /ruta/booking-service-ara-report.json \
  --kind ara --expect-questions 43
python3 scripts/verify_reports.py /ruta/booking-service-mod-report.json --kind mod
```

El verificador comprueba estructura y conteos, no vuelve a juzgar la rúbrica ni certifica el runtime. La sesión hija de ARA indicó `NO_EXIT_CRITERIA_DEFINED`; se conserva esa limitación junto a la comprobación externa de sus artefactos.

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

La evidencia agregada está en [evidence/ccs-audit.json](evidence/ccs-audit.json). No debe interpretarse la clasificación de un informe como aprobación de despliegue.

La suite pública ampliada pasó **24 pruebas, cero omitidas**, en Python 3.14.0 con la captura real. Este conteo corresponde a las herramientas de reproducción, no a 24 pruebas del negocio TravelCorp.
