# Tool Output Meter

**Vea qué salidas de herramientas llenan varias veces el contexto sin mostrar su contenido.**

[English](README.md) · [Français](README.fr.md) · [Español](README.es.md)

## Proyectos relacionados

- [Codex issue #40897](https://github.com/openai/codex/issues/40897) — Documenta un caso concreto de salida excesiva.
- [compress](https://github.com/spenmcke/compress) — Reduce salidas mediante un servicio remoto; este proyecto solo mide registros locales.
- [Codex](https://github.com/openai/codex) — Produce los registros JSONL aceptados por el analizador.

Estos enlaces describen proyectos relacionados, sin afiliación.

## Probar

```sh
python3 output_meter.py demo --lang es
```

## Qué comprueba esta herramienta

Lee registros JSONL de Codex `custom_tool_call_output` y `function_call_output`. Informa tamaños, hashes SHA-256 repetidos y marcas de truncamiento localmente.

## Usar con sus datos

```sh
python3 output_meter.py report /path/to/rollout.jsonl --lang es --json
```

Ejecute `report` sobre un registro Codex propio. Muestra cantidades y nombres de herramientas, nunca su contenido; `--json` tampoco lo incluye.

## Alcance y límites

`caracteres/4` es una estimación aproximada, no tokens reales ni facturación. El hash detecta salidas idénticas, no repeticiones semánticas. Las rutas pueden ser privadas: mantenga el informe local.

## Pruebas

```sh
python3 -m unittest discover -s tests -v
```

MIT · v0.1.0-alpha.1
