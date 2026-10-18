# Agentic Transformation Workshop

Un workshop en español para pasar de **una oportunidad de negocio a un agente funcionando**, evaluar la aplicación con ARA y MODA e integrar el trabajo en AI-DLC.

Construirás sobre un caso de reservas: el agente propone una acción, solicita aprobación, utiliza una API con PostgreSQL y recupera operaciones interrumpidas. Los pagos son simulados. El código, los ejercicios y los diagramas están incluidos bajo **MIT**.

## Empieza aquí

Necesitas **Git, Python 3.11+ y Docker** en Linux, macOS o WSL.

```bash
git clone https://github.com/sjaramillov/agentic-transformation-workshop-latam.git
cd agentic-transformation-workshop-latam
python3 booking_lab/run.py e2e --output .local/db-e2e.json
```

Verás `PASS` en los escenarios y `result: passed` en el archivo de salida. El comando prepara PostgreSQL y los servicios, recorre las operaciones y detiene sus contenedores al terminar.

**Siguiente paso:** sigue el [inicio rápido](INICIO_RAPIDO.md) y participa en la [demo del agente](AGENTE_EJECUTABLE.md).

## Qué aprenderás

| Paso | Trabaja en | Resultado |
| --- | --- | --- |
| 1. Elegir qué construir | [Ficha de valor](FICHA_VALOR.md) | Problema, métrica de éxito, alternativas y responsable |
| 2. Diseñar el proceso | [Guía A–J](GUIA_REPLICACION.md) | Eventos, oportunidad y autonomía del agente |
| 3. Ejecutar el agente | [Demo de reservas](AGENTE_EJECUTABLE.md) | Crear, consultar, cancelar y recuperar; reglas o lenguaje natural con Bedrock |
| 4. Evaluar y mejorar | [ARA y MODA con AWS Transform](EJECUCION_AWS.md) | Hallazgos priorizados, cambios y comparación |
| 5. Integrar al equipo | [AI-DLC](AI_DLC.md) | Entregables y decisiones de Inception, Construction y Operations |

La práctica local funciona sin credenciales AWS. Para Bedrock o AWS Transform necesitas acceso a esos servicios en tu cuenta; puedes seguir la [preparación de CloudShell](CLOUDSHELL.md).

## Prepara tus materiales

```bash
python3 scripts/workshop.py prepare --output .local/workshop-01
```

El comando genera la ficha de valor, los ejercicios, los contextos ARA/MODA y las fuentes de análisis desde el commit actual. También puedes explorar [un ejemplo completo](examples/workshop/README.md) sin instalar herramientas.

## Tablero del recorrido

![Del problema de negocio a una decisión con evidencia](diagramas/06-valor-ai-dlc.svg)

Abre la [galería de seis tableros](diagramas/README.md) para facilitar las sesiones de proceso, autonomía, recuperación y operación.

## Para profundizar

- [Aplicación y contrato de API](LABORATORIO_MIT.md).
- [Prompts y ejercicios](PROMPTS.md).
- [Resultados técnicos y pruebas](evidence/README.md).
- [Fuentes y recursos de AWS](RECURSOS.md).

## Licencia

Proyecto independiente inspirado en el Agentic Transformation Workshop de AWS. Las contribuciones originales se distribuyen bajo [MIT](LICENSE); consulta [autoría y referencias](NOTICE.md).
