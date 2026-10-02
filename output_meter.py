#!/usr/bin/env python3
"""Measure repeated and truncated Codex tool outputs without displaying their contents."""
import argparse
import difflib
import hashlib
import html
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path
from zipfile import ZipFile, is_zipfile

LABELS = {
    "en": ("Tool output meter", "outputs", "repeated", "truncated", "estimated tokens"),
    "fr": ("Mesure des sorties d'outils", "sorties", "répétées", "tronquées", "tokens estimés"),
    "es": ("Medidor de salidas de herramientas", "salidas", "repetidas", "truncadas", "tokens estimados"),
}
CONTEXT_LABELS = {
    "en": ("Repeated agent context", "injections", "repeated", "redundant characters", "rough text tokens"),
    "fr": ("Contexte d'agent répété", "injections", "répétées", "caractères redondants", "tokens textuels approximatifs"),
    "es": ("Contexto de agente repetido", "inyecciones", "repetidas", "caracteres redundantes", "tokens de texto aproximados"),
}
CONTEXT_ERRORS = {
    "en": {"missing": "No matching injected context found in this DSH session.", "zip": "Expected one root session JSONL in the DSH export ZIP.", "format": "Invalid DSH session JSONL at line {line}.", "path": "context requires a DSH log or export ZIP path", "zstd": "Use the official DSH export ZIP or an extracted JSONL; direct .zstd input is unsupported."},
    "fr": {"missing": "Aucun contexte injecté correspondant dans cette session DSH.", "zip": "L'export ZIP DSH doit contenir un journal JSONL de session à la racine.", "format": "Journal JSONL DSH invalide à la ligne {line}.", "path": "context exige le chemin d'un journal DSH ou d'un export ZIP", "zstd": "Utilisez l'export ZIP officiel DSH ou un JSONL extrait ; les fichiers .zstd ne sont pas lus directement."},
    "es": {"missing": "No se encontró contexto inyectado coincidente en esta sesión DSH.", "zip": "El ZIP exportado de DSH debe contener un registro JSONL de sesión en la raíz.", "format": "Registro JSONL de DSH no válido en la línea {line}.", "path": "context requiere la ruta de un registro DSH o ZIP exportado", "zstd": "Use el ZIP oficial exportado por DSH o un JSONL extraído; no se admiten archivos .zstd directamente."},
}
CONTEXT_NOTES = {
    "en": "Repeated characters count additional appended messages only. This is not provider token usage, billable cost, or proof that previous content remained visible after compaction.",
    "fr": "Les caractères répétés ne comptent que les messages ajoutés en plus. Ce n'est ni le nombre de tokens du fournisseur, ni un coût facturé, ni la preuve qu'un ancien contenu reste visible après compression.",
    "es": "Los caracteres repetidos solo cuentan mensajes añadidos de más. No son tokens del proveedor, coste facturado ni prueba de que el contenido anterior siguiera visible tras compactar.",
}
MEMORY_FRAME_END = "the newer fact supersedes the stale one in future retrieval.\n\n"
MEMORY_TAG = re.compile(r"<hindsight_memory>(.*?)</hindsight_memory>", re.IGNORECASE | re.DOTALL)
MEMORY_LABELS = {
    "en": ("Memory arrival", "turns", "with confirmed memory", "with empty memory", "unclassified", "without injection"),
    "fr": ("Arrivée des souvenirs", "tours", "avec souvenir confirmé", "avec mémoire vide", "non classés", "sans injection"),
    "es": ("Llegada de recuerdos", "turnos", "con recuerdo confirmado", "con memoria vacía", "sin clasificar", "sin inyección"),
}
MEMORY_NOTES = {
    "en": "Only the known Hindsight coding-agents 0.8.0 wrapper is classified. Other blocks remain unclassified; arrival does not prove the agent used or trusted a memory.",
    "fr": "Seul le format connu de Hindsight coding-agents 0.8.0 est classé. Les autres blocs restent non classés ; l'arrivée ne prouve pas que l'agent ait utilisé ou cru un souvenir.",
    "es": "Solo se clasifica el formato conocido de Hindsight coding-agents 0.8.0. Los demás bloques quedan sin clasificar; la llegada no prueba que el agente utilizara o creyera un recuerdo.",
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


def analyze_context(lines, kind_filter="hindsight", lang="en"):
    """Count repeated append-only DSH user/message injections without returning text."""
    groups = []
    injected = replaced = repeated = redundant = 0
    active_turn = None
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(CONTEXT_ERRORS[lang]["format"].format(line=number)) from error
        if not isinstance(record, dict):
            raise ValueError(CONTEXT_ERRORS[lang]["format"].format(line=number))
        if record.get("type") == "turn/start":
            active_turn = record.get("data", {}).get("turn") if isinstance(record.get("data"), dict) else None
            continue
        if record.get("type") == "turn/end":
            active_turn = None
            continue
        if record.get("type") != "user/message":
            continue
        data = record.get("data")
        if not isinstance(data, dict):
            continue
        source = data.get("source", {})
        source_kind = source.get("kind", "") if isinstance(source, dict) else ""
        if not isinstance(source_kind, str) or source_kind == "user" or kind_filter.lower() not in source_kind.lower():
            continue
        content = data.get("content", [])
        if not isinstance(content, list):
            continue
        text = "\n".join(block.get("text", "") for block in content
                         if isinstance(block, dict) and block.get("type") == "text" and isinstance(block.get("text"), str))
        normalized = " ".join(text.split())
        if not normalized:
            continue
        injected += 1
        if record.get("surfaceOp") != "append":
            replaced += 1
            continue
        turn = data.get("turn", active_turn)
        match = None
        for group in reversed(groups[-64:]):
            if group["source"] != source_kind:
                continue
            previous = group["sample"]
            if normalized == previous:
                match = group
                break
            if len(normalized) >= 80 and abs(len(normalized) - len(previous)) <= max(len(normalized), len(previous)) * 0.05:
                if difflib.SequenceMatcher(None, previous, normalized, autojunk=False).ratio() >= 0.97:
                    match = group
                    break
        if match is None:
            groups.append({"source": source_kind, "sample": normalized, "first_turn": turn,
                           "last_turn": turn, "events": 1, "repeated": 0})
        else:
            match["events"] += 1
            match["repeated"] += 1
            match["last_turn"] = turn
            repeated += 1
            redundant += len(text)
    if not injected:
        raise ValueError(CONTEXT_ERRORS[lang]["missing"])
    return {
        "injections": injected,
        "repeated_injections": repeated,
        "replaced_or_unverified_surface_events": replaced,
        "redundant_characters": redundant,
        "rough_text_tokens": math.ceil(redundant / 4),
        "groups": [{key: group[key] for key in ("source", "first_turn", "last_turn", "events", "repeated")}
                   for group in groups if group["repeated"]],
        "note": CONTEXT_NOTES[lang],
    }


def analyze_memory_arrival(lines, lang="en"):
    """Classify known Hindsight 0.8.0 injections by turn without returning content."""
    turns = {}
    active_turn = None
    for number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(CONTEXT_ERRORS[lang]["format"].format(line=number)) from error
        if not isinstance(record, dict):
            raise ValueError(CONTEXT_ERRORS[lang]["format"].format(line=number))
        data = record.get("data")
        data = data if isinstance(data, dict) else {}
        if record.get("type") == "turn/start":
            active_turn = data.get("turn")
            if active_turn is not None:
                turns.setdefault(str(active_turn), set())
            continue
        if record.get("type") == "turn/end":
            active_turn = None
            continue
        if record.get("type") != "user/message":
            continue
        turn = data.get("turn", active_turn)
        if turn is None:
            continue
        key = str(turn)
        statuses = turns.setdefault(key, set())
        source = data.get("source")
        source_kind = source.get("kind", "") if isinstance(source, dict) else ""
        if not isinstance(source_kind, str) or "hindsight" not in source_kind.lower():
            continue
        content = data.get("content")
        if not isinstance(content, list):
            statuses.add("unclassified")
            continue
        block_text = "\n".join(part.get("text", "") for part in content
                               if isinstance(part, dict) and part.get("type") == "text" and isinstance(part.get("text"), str))
        match = MEMORY_TAG.search(block_text)
        if not match or MEMORY_FRAME_END not in match.group(1):
            statuses.add("unclassified")
            continue
        memory = match.group(1).split(MEMORY_FRAME_END, 1)[1].strip()
        statuses.add("confirmed_memory" if memory else "empty_memory")
    if not turns:
        raise ValueError(CONTEXT_ERRORS[lang]["missing"])
    counts = Counter()
    timeline = []
    for turn, statuses in turns.items():
        if "confirmed_memory" in statuses:
            status = "confirmed_memory"
        elif "unclassified" in statuses:
            status = "unclassified"
        elif "empty_memory" in statuses:
            status = "empty_memory"
        else:
            status = "without_injection"
        counts[status] += 1
        timeline.append({"turn": turn, "status": status})
    return {"turns": len(turns), **{key: counts[key] for key in
            ("confirmed_memory", "empty_memory", "unclassified", "without_injection")},
            "timeline": timeline,
            "note": MEMORY_NOTES[lang]}


def render_memory_html(result, lang="en"):
    """A self-contained, content-free visual report for the supplied DSH export."""
    labels = {
        "en": {"title": "Memory X-Ray", "turn": "Turn", "confirmed_memory": "Memory arrived", "empty_memory": "Empty memory", "unclassified": "Unknown format", "without_injection": "No injection"},
        "fr": {"title": "Radiographie de la mémoire", "turn": "Tour", "confirmed_memory": "Souvenir arrivé", "empty_memory": "Mémoire vide", "unclassified": "Format inconnu", "without_injection": "Aucune injection"},
        "es": {"title": "Radiografía de la memoria", "turn": "Turno", "confirmed_memory": "Recuerdo recibido", "empty_memory": "Memoria vacía", "unclassified": "Formato desconocido", "without_injection": "Sin inyección"},
    }[lang]
    colors = {"confirmed_memory": "#16803c", "empty_memory": "#ca8a04", "unclassified": "#6b7280", "without_injection": "#dc2626"}
    items = "\n".join(
        f'<li><span>{html.escape(labels["turn"])} {html.escape(str(item["turn"]))}</span>'
        f'<strong style="color:{colors[item["status"]]}">{html.escape(labels[item["status"]])}</strong></li>'
        for item in result["timeline"])
    note = html.escape(result["note"])
    return ("<!doctype html><html lang=\"" + lang + "\"><meta charset=\"utf-8\"><meta name=\"viewport\" "
            "content=\"width=device-width,initial-scale=1\"><title>" + html.escape(labels["title"]) + "</title>"
            "<style>body{font:16px system-ui;max-width:760px;margin:2rem auto;padding:0 1rem;color:#17212b}"
            "li{display:flex;justify-content:space-between;gap:1rem;padding:.6rem;border-bottom:1px solid #ddd}"
            "ul{padding:0;list-style:none}small{color:#48515c}</style><h1>" + html.escape(labels["title"]) +
            "</h1><p>" + str(result["turns"]) + " " + html.escape(MEMORY_LABELS[lang][1]) +
            "</p><ul>" + items + "</ul><small>" + note + "</small></html>\n")


def read_dsh(path, lang="en"):
    """Yield the root log from an official DSH export ZIP or an extracted JSONL."""
    if path.suffix == ".zstd":
        raise ValueError(CONTEXT_ERRORS[lang]["zstd"])
    if is_zipfile(path):
        with ZipFile(path) as archive:
            names = [name for name in archive.namelist()
                     if "/" not in name and name.startswith("session") and name.endswith(".jsonl")]
            if len(names) != 1:
                raise ValueError(CONTEXT_ERRORS[lang]["zip"])
            with archive.open(names[0]) as stream:
                for line in stream:
                    yield line.decode("utf-8")
    else:
        with path.open(encoding="utf-8") as stream:
            yield from stream


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("demo", "report", "context-demo", "context", "memory-demo", "memory"))
    parser.add_argument("path", nargs="?", type=Path)
    parser.add_argument("--lang", choices=LABELS, default="en")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--html", type=Path, help="Write a local Memory X-Ray HTML report for memory commands")
    parser.add_argument("--kind", default="hindsight", help="DSH source / source DSH / fuente DSH; '' = all / toutes / todas")
    args = parser.parse_args(argv)
    if args.command == "demo":
        path = Path(__file__).parent / "fixtures" / "trace.jsonl"
    elif args.command == "context-demo":
        path = Path(__file__).parent / "fixtures" / "dsh-session.jsonl"
    elif args.command == "memory-demo":
        path = Path(__file__).parent / "fixtures" / "memory-arrival.jsonl"
    else:
        path = args.path
    if not path:
        parser.error(CONTEXT_ERRORS[args.lang]["path"] if args.command == "context" else "report requires a Codex JSONL path")
    try:
        if args.command in ("memory-demo", "memory"):
            result = analyze_memory_arrival(read_dsh(path, args.lang), args.lang)
        elif args.command in ("context-demo", "context"):
            result = analyze_context(read_dsh(path, args.lang), args.kind, args.lang)
        else:
            with path.open(encoding="utf-8") as handle:
                result = analyze(handle)
    except (OSError, ValueError, UnicodeDecodeError) as error:
        print(str(error), file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.command in ("memory-demo", "memory"):
        title, turns, present, empty, unknown, absent = MEMORY_LABELS[args.lang]
        print(title)
        print(f"{result['turns']} {turns}; {result['confirmed_memory']} {present}; "
              f"{result['empty_memory']} {empty}; {result['unclassified']} {unknown}; "
              f"{result['without_injection']} {absent}")
    elif args.command in ("context-demo", "context"):
        title, injections, repeated, chars, tokens = CONTEXT_LABELS[args.lang]
        print(title)
        print(f"{result['injections']} {injections}; {result['repeated_injections']} {repeated}")
        print(f"{result['redundant_characters']} {chars}; ~{result['rough_text_tokens']} {tokens}")
    else:
        title, outputs, repeated, truncated, tokens = LABELS[args.lang]
        print(title)
        print(f"{result['outputs']} {outputs}; {result['repeated_outputs']} {repeated}; {result['truncated_outputs']} {truncated}")
        print(f"~{result['estimated_tokens']} {tokens} (approximation)")
        for row in result["top"]:
            print(f"{row['tool']}: {row['characters']} chars")
    if args.html:
        if args.command not in ("memory-demo", "memory"):
            parser.error("--html is available only with memory or memory-demo")
        args.html.write_text(render_memory_html(result, args.lang), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
