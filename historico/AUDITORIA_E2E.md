> **Archivo histórico del 16 de octubre de 2026.** Describe otra implementación. El workshop público vigente comienza en [Inicio rápido](../INICIO_RAPIDO.md).

# Auditoría de reproducción

**Validación posterior de la réplica pública:** [17 escenarios de DB en CCS](../CCS_DATABASE_E2E.md), con compensación y auditoría durable implementadas en código original MIT. Las secciones siguientes conservan la revisión histórica.

Fecha de revisión inicial: **15 de octubre de 2026 (America/Bogota)**. Base revisada: commit `870b5f7`. La ejecución posterior del 16 de octubre UTC está documentada en [CCS_E2E.md](CCS_E2E.md); las secciones siguientes preservan el alcance y las observaciones de la auditoría inicial.

## Dictamen

**La práctica local es reproducible con la captura autorizada. La réplica AWS completa aún no está certificada de extremo a extremo.** La versión inicial era una referencia útil, pero no traía restauración, pruebas ni instrucciones suficientes para reconstruir una cuenta nueva.

El repositorio ofrece un recorrido local A–C con una entrada verificable, salidas nuevas y criterios de éxito. La ejecución posterior en CCS añadió análisis reales y comprobaciones del código generado, con fallos documentados y correcciones del empaquetado. Un clon público no incluye el paquete TravelCorp por su alcance de licencia.

## Hallazgos y correcciones

| Hallazgo observado | Impacto | Corrección / estado |
| --- | --- | --- |
| No había procedimiento de restauración | La copia podía existir sin poder reutilizarse | `lab.py restore`: hash, rutas seguras, destino nuevo y contenido comprobado |
| No se explicaba el modo offline | Parecía necesario configurar AWS incluso para A–C | Inicio rápido y `rehearse` aislado, sin dependencias pip |
| YAML/manifiesto y tableros viven en directorios distintos | Contextos ausentes o rutas equivocadas | Rutas explícitas y comprobación de ambos contextos |
| Captura de booking en rama de análisis | Riesgo de comparar o integrar la rama equivocada | Preparación Git, chequeo `doctor --live`, selección por ID |
| Sondeo con `.[0]` | Podía mostrar otra ejecución | Consultar el ID concreto |
| Faltaba sintaxis de publicación de TD | Módulo H incompleto | Comandos `-n`, `--sd`, descripción y categoría según ayuda instalada |
| `-g` dependía del directorio de trabajo | Remediación con contexto ausente o incorrecto | URI absoluta y comprobación de archivo |
| Consolidador original borra salidas y termina listeners 9090 | Pérdida de evidencias e interferencia local | Recolector nuevo, sin red ni borrado, separado por origen y con hashes |
| MODA estaba dentro del servicio, no consolidado | El resumen decía que faltaba | Localizado el conjunto original y corregido RECURSOS.md |
| MODA declara dos clasificaciones en conflicto | Comparación engañosa por tier | Divergencia conservada como evidencia pendiente de revisión |
| Reembolso mal ubicado y autonomía mal rotulada | Conceptos contradictorios | Corregidos cuadrante y escala A→P→E→G |
| Colores de texto y puntas de flecha variaban al exportar SVG | Diagramas incompletos en el render local | Rellenos explícitos y puntas vectoriales; cinco tableros revisados |
| Lectura móvil comprimía todo el tablero | Texto demasiado pequeño | Región con desplazamiento horizontal y acceso por teclado; revisión visual móvil pendiente |
| Limpieza mencionaba solo el IDE | Podía dejar otros recursos facturables | Inventario de todas las pilas y revisión posterior |

## Evidencia ejecutada

- **Archivo real:** SHA-256 `adb4440ce3a709a2b4f6718beb1115bf56f443c82b4cce8200b7d867b47271ce`; 855 entradas. Restaurado en directorios temporales nuevos.
- **Práctica:** tres fases del facilitador original con `--offline`; ocho artefactos nuevos, JSON parseables, candidato `rebooking`, autonomía `P`, contextos ARA/MODA no vacíos y vinculados al candidato.
- **Clon limpio:** se ejecutaron los comandos públicos y el flujo CLI completo, aportando el tar como entrada externa; el árbol versionado quedó limpio.
- **Conservación:** hash del manifiesto capturado sin cambios; informes recuperados por origen y bytes contrastados con el inventario; segunda ejecución sobre el mismo destino rechazada.
- **Pruebas negativas:** archivo alterado, rutas fuera del destino, enlaces simbólicos/duros, entradas especiales/duplicadas, límite de tamaño, destino existente, JSON inválido y ausencia de informes capturados.
- **Documentación:** enlaces locales, anclas de galería, textos alternativos, estructura y referencias SVG.
- **Visual:** cinco SVG renderizados mediante `sips` y revisados. La inspección no equivale a un E2E de navegador en todos los tamaños.
- **IDE AWS, solo lectura:** `atx --version` informó **3.9.0**; la ayuda confirmó `--context`, `--agent-scope`, `--prefer`, `--avoid`, `--local`, `-n`, `--sd` y `--description`. No expuso `--category` ni `--wait` en las consultas realizadas. MODA anterior figura `complete`, con finalización `2026-10-15T18:53:48.569Z`. No se volvió a ejecutar ni se canceló ese análisis.

El número y resultado final de las pruebas locales se guardan en [evidence/local-audit.json](../evidence/local-audit.json). CI ejecuta las comprobaciones públicas en Linux/macOS con Python 3.11 y 3.14. Sin el archivo privado, la prueba de captura real se marca `skipped`; ese estado no acredita el recorrido privado.

## Lo que muestra la captura

| Evidencia | Resultado observado |
| --- | --- |
| ARA precomputado | 6 BLOCKER; `Not Agent-Integrable` |
| ARA de la captura | 5 BLOCKER, 12 RISK-SAFETY, 15 RISK-QUALITY, 6 INFO; `Not Agent-Integrable` |
| MODA dentro de booking | `classification.tier = Not Ready`, pero `rule_matched` y `count_tier = Remediation Required`; `classification_consistency_check.status = divergent` |
| Rama de booking en el tar | `atx-result-staging-20261015_183919_02db4098`, HEAD `78fa7865ef08a66b10e6e74af5ce0fcdaba044eb` |
| Cambio de esa rama frente a main | Cuatro artefactos MODA; no es una remediación de aplicación |

No se corrige manualmente el informe de AWS para hacerlo coincidir con el resultado esperado. Los prompts de [PROMPTS.md](../PROMPTS.md) preservan esas discrepancias al elaborar mapeos y comparaciones.

## Pendientes identificados en la revisión inicial

1. Preparar una cuenta y versión de herramientas concretas; verificar IAM, región y modelos. Falta la plantilla self-paced original del evento.
2. Ejecutar D–E con ID, commit y contexto registrados; comprobar que los artefactos corresponden a cada ejecución.
3. Publicar versiones identificadas de ambas TD, aplicar H en copias aisladas, revisar el cambio y pasar pruebas de servicio antes de integrar.
4. Repetir I con el mismo alcance y explicar discrepancias. No basta con que la remediación tenga estado `complete`.
5. Si se pretende desplegar, comprobar plataforma, imagen, IaC, identidad, escrituras, compensación, revisión humana, observabilidad y rollback en el runtime real.

En la revisión inicial no se aprovisionó infraestructura, no se ejecutaron remediaciones cloud y no se probó una aplicación TravelCorp desplegada. Los avances posteriores y sus límites se registran en CCS_E2E.md. **No se garantiza ausencia de errores en AWS ni se presenta la práctica offline como validación de ese entorno**.

## Repetir la auditoría local

Desde el clon y con Python 3.11+:

```bash
python3 -m unittest discover -s tests -v
WORKSHOP_ARCHIVE="/ruta/a/la/captura.tar.gz" python3 -m unittest discover -s tests -v
```

Los tests de captura real invocan código del paquete autorizado en un directorio temporal. La entrada predeterminada está fijada al hash anterior. Para una captura nueva debe revisarse el contenido y su compatibilidad antes de actualizar la expectativa.
