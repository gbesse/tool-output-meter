#!/usr/bin/env python3
"""Create stable per-topic memory tags and audit a tagged export offline."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

WORDS = {
    "en": ("Topic tag", "matching records", "excluded records", "Invalid event"),
    "fr": ("Tag du sujet", "enregistrements correspondants", "enregistrements exclus", "Événement invalide"),
    "es": ("Etiqueta del tema", "registros coincidentes", "registros excluidos", "Evento no válido"),
}
NOTES = {
    "en": "Offline tag audit; it does not configure Hermes automatic recall or change a Hindsight bank.",
    "fr": "Audit hors ligne des tags ; il ne configure pas le rappel automatique de Hermes et ne modifie aucune banque Hindsight.",
    "es": "Auditoría de etiquetas sin conexión; no configura la recuperación automática de Hermes ni modifica un banco Hindsight.",
}


def topic_tag(event):
    if not isinstance(event, dict) or event.get("platform") != "telegram":
        raise ValueError("platform must be telegram")
    chat, topic = event.get("chat_id"), event.get("topic_id")
    if not isinstance(chat, (str, int)) or not str(chat) or not isinstance(topic, (str, int)) or not str(topic):
        raise ValueError("chat_id and topic_id are required")
    scope = json.dumps([str(chat), str(topic)], ensure_ascii=False, separators=(",", ":"))
    digest = hashlib.sha256(scope.encode("utf-8")).hexdigest()[:24]
    return f"telegram-topic:{digest}"


def audit(event, records, lang="en"):
    if isinstance(records, dict):
        records = records.get("records")
    if not isinstance(records, list) or not all(isinstance(row, dict) for row in records):
        raise ValueError("records must be an array of objects")
    tag = topic_tag(event)
    matches = 0
    for row in records:
        tags = row.get("tags", [])
        if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
            raise ValueError("each record needs an array of tags")
        matches += tag in tags
    return {"topic_tag": tag, "matching_records": matches, "excluded_records": len(records) - matches,
            "note": NOTES[lang]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("demo", "tag", "audit"))
    parser.add_argument("--event", type=Path)
    parser.add_argument("--records", type=Path)
    parser.add_argument("--lang", choices=WORDS, default="en")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command == "demo":
            event = {"platform": "telegram", "chat_id": 100, "topic_id": 5}
            records = [{"tags": [topic_tag(event)]}, {"tags": [topic_tag({**event, "topic_id": 6})]}]
            result = audit(event, records, args.lang)
        else:
            if args.event is None or (args.command == "audit" and args.records is None):
                parser.error("tag requires --event; audit also requires --records")
            event = json.loads(args.event.read_text(encoding="utf-8"))
            result = {"topic_tag": topic_tag(event)} if args.command == "tag" else audit(
                event, json.loads(args.records.read_text(encoding="utf-8")), args.lang)
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(f"{WORDS[args.lang][3]}: {type(error).__name__}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f"{WORDS[args.lang][0]}: {result['topic_tag']}")
        if "matching_records" in result:
            print(f"{WORDS[args.lang][1]}: {result['matching_records']}; {WORDS[args.lang][2]}: {result['excluded_records']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
