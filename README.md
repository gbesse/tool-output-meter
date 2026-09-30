# Tool Output Meter

**See which tool outputs repeatedly fill an agent’s context, without printing their contents.**

[English](README.md) · [Français](README.fr.md) · [Español](README.es.md)

## Related projects

- [Codex issue #40897](https://github.com/openai/codex/issues/40897) — Reports a concrete oversized-output incident.
- [compress](https://github.com/spenmcke/compress) — Reduces output via a remote service; this project only measures local logs.
- [Codex](https://github.com/openai/codex) — Produces the rollout records this parser accepts.

Links describe technical neighbors, not an affiliation.

## Try it

```sh
python3 output_meter.py demo --lang en
```

## What this checks

Parses Codex rollout JSONL `custom_tool_call_output` and `function_call_output` records. Reports character counts, repeated SHA-256 hashes and truncation markers locally.

## Use with your data

```sh
python3 output_meter.py report /path/to/rollout.jsonl --lang en --json
```

Run `report` on a Codex rollout you own. The tool prints counts and tool names, not output content; `--json` also omits content.

## Scope and limits

`characters/4` is a rough estimate, not actual tokens or billing. Hash repetition detects identical outputs, not semantic duplication. Log paths and error messages can still contain private information; keep reports local.

## Tests

```sh
python3 -m unittest discover -s tests -v
```

MIT · v0.1.0-alpha.1
