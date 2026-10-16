# Workshop público: empieza aquí

Todo el código, los casos, contextos y ejercicios necesarios están en este repositorio bajo MIT. Puedes ejecutarlo en tu máquina o en AWS CloudShell de tu cuenta.

## 1. Clona y comprueba el flujo con base de datos

Requisitos: Git, Python 3.11+ y Docker con el daemon activo. Docker descarga Python, PostgreSQL y Psycopg en versiones fijadas.

```bash
git clone https://github.com/sjaramillov/agentic-transformation-workshop-latam.git
cd agentic-transformation-workshop-latam
python3 -m unittest discover -s tests -v
python3 booking_lab/run.py e2e --output .local/db-e2e.json
```

El comando `run.py e2e` levanta PostgreSQL, dos API, pagos sintéticos, un worker y el ledger de auditoría; crea, consulta y cancela reservas, inyecta fallos y restaura un backup. El resultado debe decir `passed`, todos los casos deben pasar y las invariantes finales deben ser cero. Los contenedores se detienen al terminar; los datos de revisión quedan en `.local/`.

## 2. Prepara el workshop A–C y las fuentes D–I

```bash
python3 scripts/workshop.py prepare --output .local/workshop-01
```

Obtendrás los entregables de EventStorming, oportunidades y workflow, contextos ARA/MODA y dos repositorios Git aislados del servicio. El manifiesto registra commit y hashes. El comando prepara archivos sin ejecutar servicios AWS.

## 3. Completa A–J

Sigue [la guía completa](GUIA_REPLICACION.md). Para ejecutar ARA/MODA reales, prepara [CloudShell](CLOUDSHELL.md) y continúa en [Ejecución AWS](EJECUCION_AWS.md). Usa [los tableros](diagramas/README.md) para facilitar la discusión y [el contrato de la aplicación](LABORATORIO_MIT.md) para entender los controles.

## Resultado esperado

Un participante puede clonar, ejecutar, cambiar el servicio, demostrar una corrección con DB, medir con Transform y comparar los resultados usando recursos públicos. Los resultados generados en su cuenta se guardan en `.local/` para revisarlos antes de publicarlos. Eso no limita la disponibilidad del código fuente.
