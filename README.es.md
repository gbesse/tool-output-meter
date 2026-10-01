# Tool Output Meter

**Encuentre salidas de herramientas y recuerdos inyectados que llenan repetidamente el contexto, sin mostrar su contenido.**

[English](README.md) · [Français](README.fr.md) · [Español](README.es.md)

## Proyectos relacionados

- [Codex issue #40897](https://github.com/openai/codex/issues/40897) — Documenta un caso concreto de salida excesiva.
- [compress](https://github.com/spenmcke/compress) — Reduce salidas mediante un servicio remoto; este proyecto solo mide registros locales.
- [Codex](https://github.com/openai/codex) — Produce los registros JSONL aceptados por el analizador.
- [Hindsight #5026](https://github.com/vectorize-io/hindsight/issues/5026) — Describe un contexto casi idéntico inyectado en cada turno de DeepSeek Harness.
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

## Alcance y límites

`caracteres/4` es una estimación aproximada, no tokens reales ni facturación. El hash detecta salidas idénticas, no repeticiones semánticas. Las rutas pueden ser privadas: mantenga el informe local.

Para el contexto inyectado, los caracteres redundantes solo cuentan mensajes añadidos de más. No miden los tokens de entrada acumulados tras la reproducción ni prueban que el contenido anterior siguiera visible después de compactar. El comando lee ZIP exportados o JSONL simples, no archivos `.zstd` comprimidos directamente.

## Pruebas

```sh
python3 -m unittest discover -s tests -v
```

MIT · v0.1.0-alpha.1
