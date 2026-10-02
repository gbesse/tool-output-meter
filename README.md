# Tool Output Meter

**Why did my agent forget?** Inspect which memory reached each turn, which stored facts lack observation links, and when an accepted document becomes readable. Also measure repeated tool output without printing its contents.

[English](README.md) · [Français](README.fr.md) · [Español](README.es.md)

## Related projects

- [Codex issue #40897](https://github.com/openai/codex/issues/40897) — Reports a concrete oversized-output incident.
- [compress](https://github.com/spenmcke/compress) — Reduces output via a remote service; this project only measures local logs.
- [Codex](https://github.com/openai/codex) — Produces the rollout records this parser accepts.
- [Hindsight #5026](https://github.com/vectorize-io/hindsight/issues/5026) — Reports near-identical context injected on every DeepSeek Harness turn.
- [Hindsight #5082](https://github.com/vectorize-io/hindsight/issues/5082) — Reports turns with static guidance but no useful memory; the new command classifies the known wrapper.
- [Hindsight #5054](https://github.com/vectorize-io/hindsight/issues/5054) — Reports facts marked consolidated without observation links; `coverage.py` audits this exported shape.
- [Hindsight #5077](https://github.com/vectorize-io/hindsight/issues/5077) — Reports accepted writes that become visible much later; `receipt.py` polls a supplied read URL.
- [Hindsight #5073](https://github.com/vectorize-io/hindsight/issues/5073) and [Hermes Agent](https://github.com/NousResearch/hermes-agent) — Motivate the topic tag audit; `router.py` is not a live Hermes integration.
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

## Did a real memory arrive?

```sh
python3 output_meter.py memory-demo --lang en
python3 output_meter.py memory /path/to/dsh-session.zip --lang en --json
python3 output_meter.py memory /path/to/dsh-session.zip --lang en --html /tmp/memory-xray.html
```

The local report counts turns with confirmed memory text, an empty memory body, an unknown wrapper, or no Hindsight injection. It recognizes only the `hindsight_memory` wrapper and framing of Hindsight coding-agents 0.8.0; changed formats stay unknown. The demo is synthetic. Memory arrival does not prove the agent used it, and this command does not read the stored bank.

The **Memory X-Ray** HTML view is a standalone local timeline. It shows only turn labels and classification, never the memory text. Open the output file in your browser. This is a view in Tool Output Meter, not a separate integration or repository.

## Check other memory gaps

```sh
python3 coverage.py demo --lang en
python3 coverage.py check facts.json observations.json --lang en
python3 receipt.py demo --lang en
python3 receipt.py watch https://localhost:8888/documents/DOC_ID --lang en
python3 router.py demo --lang en
python3 router.py audit --event fixtures/event.json --records fixtures/records.json --lang en
```

`coverage.py` reads fact and observation JSON exported from a bank you control; a marked but unlinked fact is a **candidate** gap. It rejects observations missing `source_memory_ids`. `receipt.py` makes read-only GET requests to the exact document URL you supply and distinguishes delayed 404 from 403; an optional bearer token is read from `--token-env VARIABLE` and is never printed. `router.py` creates stable pseudonymous tags from a Telegram chat and topic, then audits a local tagged export. It does **not** configure Hermes automatic recall, and its hashes are not an access-control boundary. These commands share one home so a user diagnosing lost memory can move from injection to stored coverage, delayed visibility and topic separation. Their demos are synthetic; only the GET command talks to a user-specified endpoint.

## Scope and limits

`characters/4` is a rough estimate, not actual tokens or billing. Hash repetition detects identical outputs, not semantic duplication. Log paths and error messages can still contain private information; keep reports local.

For injected context, redundant characters count extra appended messages only. They do not measure the cumulative input tokens after replay or prove that older content remained visible after compaction. The current command reads export ZIP or plain JSONL, not compressed `.zstd` files directly.

## Tests

```sh
python3 -m unittest discover -s tests -v
```

MIT · v0.1.2-alpha.1
