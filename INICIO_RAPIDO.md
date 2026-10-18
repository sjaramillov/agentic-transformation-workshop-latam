# Empieza el workshop

Puedes realizar la práctica en tu máquina o en AWS CloudShell. El repositorio incluye código, ejercicios, plantillas y diagramas bajo MIT.

## Elige un recorrido

| Recorrido | Necesitas | Obtendrás |
| --- | --- | --- |
| Decisión de negocio | [Ficha de valor](FICHA_VALOR.md) | Hipótesis, métrica, alternativas y responsable |
| Agente de reservas | Python 3.11+, Git y Docker | Crear, consultar y cancelar con aprobación y PostgreSQL |
| Agente con lenguaje natural | Lo anterior, AWS CLI y acceso a Bedrock | El mismo flujo con un modelo de lenguaje |
| Evaluación de aplicaciones | Cuenta AWS y acceso a AWS Transform | Informes ARA/MODA y plan de mejoras |

## 1. Clona y ejecuta

Con Docker activo, en Linux, macOS o WSL:

```bash
git clone https://github.com/sjaramillov/agentic-transformation-workshop-latam.git
cd agentic-transformation-workshop-latam
python3 booking_lab/run.py e2e --output .local/db-e2e.json
```

La primera ejecución descarga las imágenes. El comando levanta PostgreSQL, dos API, pagos simulados, un worker y auditoría. Recorre creación, consulta, cancelación y recuperación.

**Resultado esperado:** cada escenario imprime `PASS`, el JSON indica `result: passed` y los contenedores quedan detenidos. Los archivos de la práctica se guardan en `.local/`.

## 2. Usa el agente

```bash
python3 booking_lab/run.py demo --output .local/demo.json
```

Espera `DEMO_READY` y sigue la [demo paso a paso](AGENTE_EJECUTABLE.md) en una segunda terminal: propón una reserva, apruébala, consulta y cancela con otra aprobación. Esa guía incluye la opción de usar Bedrock para interpretar lenguaje natural.

## 3. Genera los ejercicios

```bash
python3 scripts/workshop.py prepare --output .local/workshop-01
```

Obtendrás la ficha de valor, EventStorming, oportunidades, workflow, entregables de AI-DLC, contextos ARA/MODA y dos clones para análisis. El preparador toma el commit actual; registra tus cambios en Git antes de generar otra práctica y elige un directorio nuevo.

Puedes consultar [el ejemplo resuelto](examples/workshop/README.md) como punto de partida.

## 4. Completa el recorrido

1. Define el problema y la métrica en la [ficha de valor](FICHA_VALOR.md).
2. Sigue los módulos de la [guía A–J](GUIA_REPLICACION.md) con los [tableros](diagramas/README.md).
3. Prepara [CloudShell](CLOUDSHELL.md) y ejecuta [ARA/MODA](EJECUCION_AWS.md).
4. Prioriza, implementa una mejora y vuelve a evaluar.
5. Organiza los entregables y la medición de resultados con [AI-DLC](AI_DLC.md).

Al terminar tendrás un agente ejecutable, una aplicación evaluada y un plan de trabajo conectado con una métrica de negocio.
