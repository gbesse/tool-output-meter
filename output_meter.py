#!/usr/bin/env python3
"""Measure repeated and truncated Codex tool outputs without displaying their contents."""
import argparse
import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path

LABELS = {
    "en": ("Tool output meter", "outputs", "repeated", "truncated", "estimated tokens"),
    "fr": ("Mesure des sorties d'outils", "sorties", "répétées", "tronquées", "tokens estimés"),
    "es": ("Medidor de salidas de herramientas", "salidas", "repetidas", "truncadas", "tokens estimados"),
}
MARKERS = ("Warning: truncated output", "tokens truncated", "characters truncated")


def analyze(lines):
    names = {}
    outputs = []
    usage_records = 0
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"invalid JSONL at line {number}: {error.msg}") from error
        if not isinstance(record, dict):
            continue
        payload = record.get("payload", {})
        if not isinstance(payload, dict):
            continue
        if record.get("type") == "token_usage_record":
            usage_records += 1
        if record.get("type") != "response_item":
            continue
        kind = payload.get("type")
        call_id = str(payload.get("call_id", ""))
        if kind in ("custom_tool_call", "function_call"):
            names[call_id] = str(payload.get("name", "unknown"))
        if kind not in ("custom_tool_call_output", "function_call_output"):
            continue
        raw = payload.get("output", "")
        if not isinstance(raw, str):
            raw = json.dumps(raw, ensure_ascii=False)
        outputs.append({"tool": names.get(call_id, "unknown"), "characters": len(raw),
                        "estimated_tokens": math.ceil(len(raw) / 4),
                        "sha256": hashlib.sha256(raw.encode()).hexdigest(),
                        "truncated": any(marker in raw for marker in MARKERS)})
    if not outputs:
        raise ValueError("no Codex tool outputs found")
    counts = Counter(row["sha256"] for row in outputs)
    total_characters = sum(row["characters"] for row in outputs)
    return {"outputs": len(outputs), "characters": total_characters,
            "estimated_tokens": sum(row["estimated_tokens"] for row in outputs),
            "repeated_outputs": sum(counts[row["sha256"]] > 1 for row in outputs),
            "truncated_outputs": sum(row["truncated"] for row in outputs),
            "usage_records_seen": usage_records,
            "top": [{"tool": row["tool"], "characters": row["characters"],
                     "estimated_tokens": row["estimated_tokens"], "repeated": counts[row["sha256"]] > 1,
                     "truncated": row["truncated"]} for row in sorted(outputs, key=lambda row: row["characters"], reverse=True)[:5]],
            "note": "Characters/4 is a rough estimate, not a provider token count or billing measure. Output content is never printed."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("demo", "report"))
    parser.add_argument("path", nargs="?", type=Path)
    parser.add_argument("--lang", choices=LABELS, default="en")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    path = Path(__file__).parent / "fixtures" / "trace.jsonl" if args.command == "demo" else args.path
    if not path:
        parser.error("report requires a Codex JSONL path")
    try:
        with path.open(encoding="utf-8") as handle:
            result = analyze(handle)
    except (OSError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        title, outputs, repeated, truncated, tokens = LABELS[args.lang]
        print(title)
        print(f"{result['outputs']} {outputs}; {result['repeated_outputs']} {repeated}; {result['truncated_outputs']} {truncated}")
        print(f"~{result['estimated_tokens']} {tokens} (approximation)")
        for row in result["top"]:
            print(f"{row['tool']}: {row['characters']} chars")
    return 0


if __name__ == "__main__":
    sys.exit(main())
