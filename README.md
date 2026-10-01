# Tool Output Meter

**Find tool outputs and injected memory blocks that repeatedly fill an agent's context, without printing their contents.**

[English](README.md) · [Français](README.fr.md) · [Español](README.es.md)

## Related projects

- [Codex issue #40897](https://github.com/openai/codex/issues/40897) — Reports a concrete oversized-output incident.
- [compress](https://github.com/spenmcke/compress) — Reduces output via a remote service; this project only measures local logs.
- [Codex](https://github.com/openai/codex) — Produces the rollout records this parser accepts.
- [Hindsight #5026](https://github.com/vectorize-io/hindsight/issues/5026) — Reports near-identical context injected on every DeepSeek Harness turn.
- [DeepSeek Harness session export](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/session-query/session-log-export/README.md) — Documents the ZIP containing the session JSONL read by the new context command.

Links describe technical neighbors, not an affiliation.

## Try it

```sh
python3 output_meter.py demo --lang en
python3 output_meter.py context-demo --lang en
```

## What this checks

Parses Codex rollout JSONL `custom_tool_call_output` and `function_call_output` records. Reports character counts, repeated SHA-256 hashes and truncation markers locally.

## Use with your data

```sh
python3 output_meter.py report /path/to/rollout.jsonl --lang en --json
```

Run `report` on a Codex rollout you own. The tool prints counts and tool names, not output content; `--json` also omits content.

## Find repeated injected context

In DeepSeek Harness Web, choose **Download session log** or `/export`, then run:

```sh
python3 output_meter.py context /path/to/dsh-session.zip --lang en
python3 output_meter.py context /path/to/session.v4.jsonl --lang en --json
```

The command reads the root session JSONL from the official export ZIP or an extracted JSONL. By default it selects non-human `user/message` events whose `source.kind` contains `hindsight`. Use `--kind ''` for all injected sources. It counts appended identical or at least 97%-similar blocks from the same source; replacements and events without a confirmed append surface are excluded from the redundancy total. It never prints the block text. The demo is synthetic. We checked the parser on [DeepSeek Harness's public V4 session snapshot](https://github.com/deepseek-ai/deepseek-harness/blob/master/snapshots/web/permission-policy-context/session.v4.jsonl) with `--kind ''`; it has **not** been run on the affected Hindsight user's session.

## Scope and limits

`characters/4` is a rough estimate, not actual tokens or billing. Hash repetition detects identical outputs, not semantic duplication. Log paths and error messages can still contain private information; keep reports local.

For injected context, redundant characters count extra appended messages only. They do not measure the cumulative input tokens after replay or prove that older content remained visible after compaction. The current command reads export ZIP or plain JSONL, not compressed `.zstd` files directly.

## Tests

```sh
python3 -m unittest discover -s tests -v
```

MIT · v0.1.0-alpha.1
