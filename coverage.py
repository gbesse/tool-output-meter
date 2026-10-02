#!/usr/bin/env python3
"""Audit whether marked Hindsight facts are linked from any observation."""
import argparse
import json
import sys
from pathlib import Path

WORDS = {
    "en": ("facts", "represented", "marked but unlinked", "pending", "unknown source links", "Invalid input"),
    "fr": ("faits", "représentés", "marqués mais sans lien", "en attente", "liens vers sources inconnues", "Entrée invalide"),
    "es": ("hechos", "representados", "marcados pero sin enlace", "pendientes", "enlaces a fuentes desconocidas", "Entrada no válida"),
}
NOTES = {
    "en": "A marked, unlinked fact is a candidate gap, not proof that its meaning was lost. No source text is printed.",
    "fr": "Un fait marqué sans lien est une lacune possible, pas la preuve que son sens est perdu. Aucun texte source n'est affiché.",
    "es": "Un hecho marcado sin enlace es una posible brecha, no prueba de pérdida de significado. No se muestra texto fuente.",
}


def rows(value, key):
    if isinstance(value, dict):
        value = value.get(key)
    if not isinstance(value, list):
        raise ValueError(f"expected a JSON array or object with '{key}' array")
    if not all(isinstance(item, dict) for item in value):
        raise ValueError(f"'{key}' must contain objects")
    return value


def audit(facts_data, observations_data, lang="en"):
    facts = rows(facts_data, "facts")
    observations = rows(observations_data, "observations")
    ids = set()
    marked = set()
    for fact in facts:
        identity = fact.get("id")
        if not isinstance(identity, (str, int)) or not str(identity):
            raise ValueError("each fact needs an id")
        identity = str(identity)
        if identity in ids:
            raise ValueError("duplicate fact id")
        ids.add(identity)
        if fact.get("consolidated_at") is not None:
            marked.add(identity)
    linked = set()
    for observation in observations:
        if "source_memory_ids" not in observation:
            raise ValueError("each observation must include source_memory_ids; an omitted field is not an empty list")
        source_ids = observation["source_memory_ids"]
        if not isinstance(source_ids, list) or not all(isinstance(x, (str, int)) for x in source_ids):
            raise ValueError("source_memory_ids must be an array of ids")
        linked.update(str(x) for x in source_ids)
    return {
        "facts": len(ids),
        "represented": len(ids & linked),
        "marked_but_unlinked": len(marked - linked),
        "pending_unlinked": len((ids - marked) - linked),
        "unknown_source_links": len(linked - ids),
        "note": NOTES[lang],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("demo", "check"))
    parser.add_argument("facts", nargs="?", type=Path)
    parser.add_argument("observations", nargs="?", type=Path)
    parser.add_argument("--lang", choices=WORDS, default="en")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "demo":
        root = Path(__file__).parent / "fixtures"
        facts_path, observations_path = root / "facts.json", root / "observations.json"
    else:
        if args.facts is None or args.observations is None:
            parser.error("check requires facts and observations JSON paths")
        facts_path, observations_path = args.facts, args.observations
    try:
        result = audit(json.loads(facts_path.read_text(encoding="utf-8")),
                       json.loads(observations_path.read_text(encoding="utf-8")), args.lang)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"{WORDS[args.lang][5]}: {error}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        labels = WORDS[args.lang]
        for key, label in zip(("facts", "represented", "marked_but_unlinked", "pending_unlinked", "unknown_source_links"), labels):
            print(f"{label}: {result[key]}")
    return 0 if args.command == "demo" or result["marked_but_unlinked"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
