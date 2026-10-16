> **Archivo histórico del 16 de octubre de 2026.** Describe otra implementación. El workshop público vigente comienza en [Inicio rápido](../INICIO_RAPIDO.md).

# Revisión de las definiciones de transformación del taller

Esta revisión corresponde a las TD y al código inicial de la captura autorizada del 15 de octubre de 2026. Son **hallazgos de revisión de sus ejemplos**, no resultados de pruebas sobre una remediación nueva. El código generado por ATX puede variar y debe examinarse por separado.

## Criterios que deben cumplirse antes de aceptar H

| Punto observado | Consecuencia si el generador conserva el ejemplo | Comprobación y corrección necesarias |
| --- | --- | --- |
| La TD de contenedores propone sonda HTTP en `/`; el PHP inicial termina esa ruta con 404 y abre la base de datos antes de resolver rutas | La imagen puede compilar y quedar permanentemente no disponible | Probar la ruta elegida con dependencias configuradas; definir liveness y readiness explícitos y comprobar fallo de DB |
| La TD de idempotencia guarda la respuesta desde un callback de cierre, mientras el PHP inicial llama a `$conn->close()` al terminar normalmente | El callback puede usar una conexión cerrada y dejar la clave en `in_progress` | Probar POST/PUT/DELETE exitosos y fallidos, comprobar fila persistida y replay; completar el registro antes de cerrar la conexión |
| La clave de deduplicación propuesta depende solo del encabezado; no incluye identidad, ruta ni huella del cuerpo | Reutilizar una clave para otra petición puede reproducir una respuesta equivocada | Delimitar la clave por identidad/operación, comparar huella del cuerpo y rechazar reutilización incompatible; probar concurrencia y recuperación de solicitudes interrumpidas |
| El ejemplo de API Gateway agrega API, integración, ruta y JWT, pero no muestra un Stage; la ruta tampoco exige scopes | La plantilla puede estar incompleta y autenticación no acredita autorización por operación | Validar IaC, Stage, scopes de lectura/escritura, expiración, emisor y audiencia con pruebas positivas y negativas |
| El backend original admite HTTP público y no valida identidad de máquina dentro de PHP | Agregar una puerta de entrada autenticada no elimina un acceso directo al backend | Demostrar que el origen solo acepta tráfico por el camino autorizado y que saltarse el gateway falla; revisar la integración privada si se usa EKS |
| La TD combina CloudTrail/Object Lock con `error_log()` y usa `session_id()` como principal | No demuestra una auditoría durable de cada llamada de negocio atribuida al cliente M2M | Configurar access logs del API y eventos de aplicación con identidad validada, correlación, entrega, retención y prueba de consulta |
| La TD describe tags de RDS como imposición de residencia y el enmascarado como eliminación del problema de transferencias | Una declaración documental puede confundirse con un control efectivo | Verificar políticas, regiones, réplicas, logs, exportaciones y destinos; evaluar qué datos siguen identificando personas tras el enmascarado |
| El procesador de pagos del código es un dominio de ejemplo y el paquete inicial no aporta un recorrido completo con datos de prueba | Restaurar archivos o construir una imagen no produce por sí solo reservas funcionales | Preparar esquema y datos sintéticos, un doble de pagos controlable y pruebas de compensación; no usar tarjetas ni reservas reales |

Estos criterios se aplican a la salida generada. Una etiqueta `Pilot-Ready` o cero bloqueadores en un informe no reemplaza esas pruebas.

## Referencias técnicas

- [Access logs de HTTP API](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-logging.html): registrar accesos a la API requiere configuración propia de logging.
- [API Gateway y CloudTrail](https://docs.aws.amazon.com/apigateway/latest/developerguide/cloudtrail.html): evidencia de las operaciones del servicio AWS; revisar separadamente las peticiones de negocio de la aplicación.
- [Tags como metadatos](https://docs.aws.amazon.com/whitepapers/latest/tagging-best-practices/what-are-tags.html): los pares clave/valor necesitan controles que interpreten y hagan cumplir una política.

No se despliega la infraestructura de ejemplo como parte de la validación local. Las pruebas de una aplicación desplegada requieren un entorno y criterios adicionales descritos en [EJECUCION_AWS.md](EJECUCION_AWS.md).

## Validación ejecutada de la plantilla de plataforma

En CloudShell se ejecutó **cfn-lint 1.57.2** sobre `platform-team/deploy-pipeline.yaml` de la captura. Devolvió dos errores:

- `E3032`, línea 64: `Stages.Source.Actions` es una lista vacía; debe contener al menos una acción.
- `E3702`, línea 67: la acción de Build con CodeBuild no declara `InputArtifacts`.

El propio archivo indica que la fuente se conectaría en una cuenta real. Antes de desplegar hay que elegir e implementar esa conexión y los contratos de artefactos, configurar el registro/etiqueta de imagen, permisos, acceso a EKS y referencias de imagen. Cambiar solo las dos propiedades para silenciar el validador no completaría ese trabajo. Esta prueba acredita que **el pipeline capturado no es desplegable tal cual**; no se aplicó ninguna pila AWS.

El mismo validador encontró en `platform-team/booking-service-eks.yaml` el error `E3691` por `EngineVersion: '8.0'` (no coincide con una versión completa de su catálogo), y `W2501` por contraseña embebida. Debe seleccionarse una versión realmente disponible en la región y preparar la entrega de secretos antes de desplegar; la validación estática no sustituye esa comprobación con RDS.

## Contraste con la segunda TD ejecutada en CCS

La salida nueva conservó el callback que usa la conexión cerrada. El [probe de regresión](RUNTIME_LOCAL.md) lo reprodujo y comprobó una corrección de ese orden. También se observó que la plantilla generada sigue sin Stage de API Gateway ni `AuthorizationScopes` en la ruta. cfn-lint volvió a informar `E3691` y `W2501`. Estas observaciones se añaden a la revisión inicial; un parseo YAML satisfactorio no basta para aceptar la infraestructura.
