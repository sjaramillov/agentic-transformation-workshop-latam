# Resultados técnicos

| Recorrido | Resultado | Consulta |
| --- | --- | --- |
| Práctica web sin instalación | 21 situaciones, persistencia y descargas; recorrido completo en Chromium, WebKit y móvil | [Pruebas reproducibles](../workshop/web/README.md#validar-un-cambio) · artefacto `browser-e2e-evidence` en [CI](https://github.com/sjaramillov/agentic-transformation-workshop-latam/actions/workflows/checks.yml) |
| Discovery con cliente, coach y tableros | 21 situaciones; tres tableros; preparación ARA/MODA desde un clon limpio | [Validación del recorrido](discovery/README.md) |
| Suite del discovery local original | 123 pruebas aprobadas en esa revisión | [Evidencia](discovery/verification.json) y [CI actual](https://github.com/sjaramillov/agentic-transformation-workshop-latam/actions/workflows/checks.yml) |
| Agente con Bedrock y PostgreSQL | 7/7 escenarios con Nova Micro | [Resumen y ejecución](bedrock/README.md) |
| Aplicación y agente determinista | 28/28 escenarios en dos ejecuciones | [Primera](bedrock/database-e2e-1.json) y [segunda](bedrock/database-e2e-2.json) |
| Suite anterior al discovery | 112 pruebas; Linux/macOS | [CI de esa revisión](https://github.com/sjaramillov/agentic-transformation-workshop-latam/actions/runs/39133062523) |

Para ejecutar tus propias comprobaciones, sigue [Pruebas del workshop](../AUDITORIA_E2E.md). Para comenzar la práctica, vuelve a [Inicio rápido](../INICIO_RAPIDO.md).

## Referencias de evaluación

Los informes ARA/MODA incluyen la revisión analizada y sirven como ejemplo de comparación: [evaluación de aplicaciones](../CCS_E2E.md). Para generar resultados sobre tu versión sigue [Ejecución AWS](../EJECUCION_AWS.md).

Las ejecuciones anteriores se conservan en [el registro técnico de Bedrock](bedrock/HISTORIAL.md), [la validación anterior del agente](agent-workshop/README.md) y [el archivo histórico](../historico/README.md).
