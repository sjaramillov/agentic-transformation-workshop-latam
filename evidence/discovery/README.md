# Validación del discovery

Validado el **19 de octubre de 2026**, sobre la revisión [`f0850cb`](https://github.com/sjaramillov/agentic-transformation-workshop-latam/commit/f0850cbdc0a85d489cca309d0e8839bfa51ab4fc).

| Comprobación | Resultado |
| --- | --- |
| Recorrido en navegador | 21 situaciones completadas con respuestas variadas; cliente y coach visibles |
| Tableros progresivos | Proceso, cuadrantes y carriles; 45 notas y cuatro operaciones API al completar |
| Continuidad y acceso | Recarga con feedback pendiente, reanudación, teclado y pantalla de 390 px |
| Exportación | Conversación, sesión, contextos y tableros autocontenidos disponibles |
| Clon limpio | CLI → 21 situaciones → preparación de ARA/MODA; hashes de contextos y ambas fuentes comprobados |
| Suite automatizada | 123 pruebas aprobadas; incluye rutas completas, persistencia, límites HTTP y enlaces de la guía |

La prueba desde un clon limpio utilizó exclusivamente los archivos públicos del repositorio. Los tableros exportados también se comprobaron sin conexión. [Resultado estructurado](verification.json).

## Repetir la validación

```bash
python3 -m unittest discover -s tests -v
python3 scripts/facilitate.py --output .local/discovery-check
```

Sigue la [lista del recorrido](../../AUDITORIA_E2E.md#0-cliente-coach-y-tableros) y completa la preparación con esa sesión. Para revisar el caso terminado puedes descargar los [tableros de ejemplo](../../examples/discovery/tableros.html) y leer la [conversación](../../examples/discovery/conversacion.md).

El [workflow de GitHub](https://github.com/sjaramillov/agentic-transformation-workshop-latam/actions/workflows/checks.yml) ejecuta la suite en Linux/macOS y dos repeticiones del E2E con PostgreSQL. Las ejecuciones de AWS Transform y Bedrock tienen su [evidencia propia](../README.md).
