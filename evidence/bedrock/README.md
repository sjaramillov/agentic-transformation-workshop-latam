# Resultados de validación con Bedrock

El agente se validó con **Amazon Nova Micro en Bedrock**, PostgreSQL 16.15 y AWS CloudShell en `us-east-1`, el 18 de octubre de 2026.

| Comprobación | Resultado | Referencia |
| --- | --- | --- |
| Agente con Bedrock y PostgreSQL | 7/7 escenarios; cuatro inferencias | [Resultado de ejecución](bedrock-live-03.json) |
| Creación, consulta y cancelación | Aprobación antes de escribir, aislamiento por usuario y un reembolso | Mismo resultado |
| Recuperación | Mismo plan, sin otra inferencia ni doble cobro | Mismo resultado |
| Restauración y cierre | Seis tablas restauradas; seis contenedores detenidos | Mismo resultado |
| Pruebas automatizadas | 112 pruebas y dos ejecuciones de 28 escenarios de DB | [CI](https://github.com/sjaramillov/agentic-transformation-workshop-latam/actions/runs/39133062523) |

## Ejecutarlo en tu cuenta

Necesitas Python 3.11+, Docker, AWS CLI y acceso al modelo. La ejecución utiliza Bedrock y genera consumo AWS; los pagos del laboratorio son simulados.

```bash
python3 booking_lab/bedrock_e2e.py \
  --live-bedrock --confirm-test-operator \
  --model-id amazon.nova-micro-v1:0 --region us-east-1 \
  --output .local/bedrock-live-01.json
```

**Resultado esperado:** `result: passed`, siete escenarios aprobados y `cleanup.result: passed`. Usa un archivo de salida nuevo en cada ejecución. La opción `--confirm-test-operator` aprueba automáticamente solo las acciones exactas previstas por la prueba.

Para revisar las propuestas manualmente, sigue la [guía del agente](../../AGENTE_EJECUTABLE.md). Para configurar el entorno, consulta [CloudShell](../../CLOUDSHELL.md).

## Referencia técnica

- [Comprobaciones y hashes](verification.json).
- [Resultados de DB: primera](database-e2e-1.json) y [segunda ejecución](database-e2e-2.json).
- [Checksums de los resultados](SHA256SUMS).
- [Registro técnico de desarrollo](HISTORIAL.md).

Estas pruebas cubren los escenarios del laboratorio con datos sintéticos. El ensayo de valor de negocio se define en la [ficha de valor](../../FICHA_VALOR.md).
