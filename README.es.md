# Tool Output Meter

**¿Por qué olvidó mi agente?** Vea qué recuerdos llegan a cada turno, qué hechos almacenados no tienen enlaces a observaciones y cuándo puede leerse un documento aceptado. Mida también las salidas repetidas de herramientas sin mostrar su contenido.

[English](README.md) · [Français](README.fr.md) · [Español](README.es.md)

## Proyectos relacionados

- [Codex issue #40897](https://github.com/openai/codex/issues/40897) — Documenta un caso concreto de salida excesiva.
- [compress](https://github.com/spenmcke/compress) — Reduce salidas mediante un servicio remoto; este proyecto solo mide registros locales.
- [Codex](https://github.com/openai/codex) — Produce los registros JSONL aceptados por el analizador.
- [Hindsight #5026](https://github.com/vectorize-io/hindsight/issues/5026) — Describe un contexto casi idéntico inyectado en cada turno de DeepSeek Harness.
- [Hindsight #5082](https://github.com/vectorize-io/hindsight/issues/5082) — Describe turnos con instrucciones estáticas pero sin recuerdo útil; el nuevo comando clasifica ese formato conocido.
- [Hindsight #5054](https://github.com/vectorize-io/hindsight/issues/5054) — Describe hechos marcados como consolidados sin enlaces de observación; `coverage.py` audita esa exportación.
- [Hindsight #5077](https://github.com/vectorize-io/hindsight/issues/5077) — Describe escrituras aceptadas que aparecen mucho más tarde; `receipt.py` consulta una URL de lectura proporcionada.
- [Hindsight #5073](https://github.com/vectorize-io/hindsight/issues/5073) y [Hermes Agent](https://github.com/NousResearch/hermes-agent) — Motivan la auditoría de etiquetas por tema; `router.py` no es una integración Hermes en vivo.
- [Exportación de sesiones de DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/session-query/session-log-export/README.md) — Documenta el ZIP con el registro JSONL leído por el nuevo comando.

Estos enlaces describen proyectos relacionados, sin afiliación.

## Probar

```sh
python3 output_meter.py demo --lang es
python3 output_meter.py context-demo --lang es
```

## Qué comprueba esta herramienta

Lee registros JSONL de Codex `custom_tool_call_output` y `function_call_output`. Informa tamaños, hashes SHA-256 repetidos y marcas de truncamiento localmente.

## Usar con sus datos

```sh
python3 output_meter.py report /path/to/rollout.jsonl --lang es --json
```

Ejecute `report` sobre un registro Codex propio. Muestra cantidades y nombres de herramientas, nunca su contenido; `--json` tampoco lo incluye.

## Encontrar contexto inyectado repetidamente

En DeepSeek Harness Web, elija **Download session log** o `/export` y ejecute:

```sh
python3 output_meter.py context /ruta/a/dsh-session.zip --lang es
python3 output_meter.py context /ruta/a/session.v4.jsonl --lang es --json
```

El comando lee el JSONL de la sesión raíz desde el ZIP oficial o un JSONL extraído. Por defecto selecciona eventos `user/message` no humanos cuyo `source.kind` contiene `hindsight`. `--kind ''` incluye todas las fuentes inyectadas. Cuenta bloques añadidos idénticos o al menos un 97 % similares de la misma fuente; los reemplazos y eventos sin adición confirmada no aumentan el total redundante. Nunca muestra el texto. La demostración es sintética. Comprobamos el analizador con [un registro V4 público de DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness/blob/master/snapshots/web/permission-policy-context/session.v4.jsonl) usando `--kind ''`, pero **no con la sesión de quien abrió la issue Hindsight**.

## ¿Llegó un recuerdo real?

```sh
python3 output_meter.py memory-demo --lang es
python3 output_meter.py memory /ruta/a/dsh-session.zip --lang es --json
python3 output_meter.py memory /ruta/a/dsh-session.zip --lang es --html /tmp/memory-xray.html
```

El informe local cuenta turnos con recuerdo confirmado, memoria vacía, formato desconocido o sin inyección Hindsight. Reconoce solo el formato `hindsight_memory` de Hindsight coding-agents 0.8.0; un formato cambiado queda sin clasificar. La demostración es sintética. La llegada no prueba que el agente usara el recuerdo y este comando no lee el banco almacenado.

La vista HTML **Memory X-Ray** es una cronología local autónoma. Muestra solo los números de turno y su clase, nunca el texto de los recuerdos. Abra el archivo generado en su navegador. Es una vista de Tool Output Meter, no una integración ni un repositorio separado.

## Comprobar otras pérdidas de memoria

```sh
python3 coverage.py demo --lang es
python3 coverage.py check facts.json observations.json --lang es
python3 receipt.py demo --lang es
python3 receipt.py watch https://localhost:8888/documents/DOC_ID --lang es
python3 router.py demo --lang es
python3 router.py audit --event fixtures/event.json --records fixtures/records.json --lang es
```

`coverage.py` lee JSON de hechos y observaciones exportados de un banco propio; un hecho marcado sin enlace es una brecha **posible**. Rechaza observaciones sin `source_memory_ids`. `receipt.py` solo hace GET a la URL exacta proporcionada y distingue un 404 tardío de un 403; un token opcional se lee con `--token-env VARIABLE` y nunca se muestra. `router.py` crea etiquetas seudónimas estables a partir de un chat y un tema de Telegram, y audita una exportación local. **No** configura la recuperación automática de Hermes y sus hashes no son un control de acceso. Los comandos permiten pasar de la inyección a la cobertura, la visibilidad tardía y la separación de temas. Las demostraciones son sintéticas; solo el comando GET contacta una URL proporcionada por el usuario.

## Alcance y límites

`caracteres/4` es una estimación aproximada, no tokens reales ni facturación. El hash detecta salidas idénticas, no repeticiones semánticas. Las rutas pueden ser privadas: mantenga el informe local.

Para el contexto inyectado, los caracteres redundantes solo cuentan mensajes añadidos de más. No miden los tokens de entrada acumulados tras la reproducción ni prueban que el contenido anterior siguiera visible después de compactar. El comando lee ZIP exportados o JSONL simples, no archivos `.zstd` comprimidos directamente.

## Pruebas

```sh
python3 -m unittest discover -s tests -v
```

MIT · v0.1.2-alpha.1
