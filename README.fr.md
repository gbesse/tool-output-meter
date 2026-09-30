# Tool Output Meter

**Voyez quelles sorties d’outils remplissent plusieurs fois le contexte sans afficher leur contenu.**

[English](README.md) · [Français](README.fr.md) · [Español](README.es.md)

## Projets voisins

- [Codex issue #40897](https://github.com/openai/codex/issues/40897) — Documente un cas concret de sorties trop volumineuses.
- [compress](https://github.com/spenmcke/compress) — Réduit les sorties via un service distant ; ce dépôt mesure seulement des journaux locaux.
- [Codex](https://github.com/openai/codex) — Produit les enregistrements JSONL lus par le parseur.

Ces liens décrivent des projets voisins, sans affiliation.

## Essayer

```sh
python3 output_meter.py demo --lang fr
```

## Ce que cet outil vérifie

Lit les entrées Codex JSONL `custom_tool_call_output` et `function_call_output`. Rapporte tailles, hachages SHA-256 répétés et marqueurs de troncation en local.

## Utiliser avec vos données

```sh
python3 output_meter.py report /path/to/rollout.jsonl --lang fr --json
```

Lancez `report` sur un journal Codex que vous possédez. L’outil affiche nombres et noms d’outils, jamais les sorties ; `--json` omet aussi leur contenu.

## Périmètre et limites

`caractères/4` est une estimation grossière, sans lien direct avec la facturation. Le hachage détecte des sorties identiques, pas des répétitions sémantiques. Les chemins peuvent rester privés : gardez le rapport en local.

## Tests

```sh
python3 -m unittest discover -s tests -v
```

MIT · v0.1.0-alpha.1
