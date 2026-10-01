# Tool Output Meter

**Repérez les sorties d'outils et les souvenirs injectés qui remplissent plusieurs fois le contexte, sans afficher leur contenu.**

[English](README.md) · [Français](README.fr.md) · [Español](README.es.md)

## Projets voisins

- [Codex issue #40897](https://github.com/openai/codex/issues/40897) — Documente un cas concret de sorties trop volumineuses.
- [compress](https://github.com/spenmcke/compress) — Réduit les sorties via un service distant ; ce dépôt mesure seulement des journaux locaux.
- [Codex](https://github.com/openai/codex) — Produit les enregistrements JSONL lus par le parseur.
- [Hindsight #5026](https://github.com/vectorize-io/hindsight/issues/5026) — Signale un contexte presque identique injecté à chaque tour de DeepSeek Harness.
- [Export de session DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/session-query/session-log-export/README.md) — Documente le ZIP contenant le journal JSONL lu par la nouvelle commande.

Ces liens décrivent des projets voisins, sans affiliation.

## Essayer

```sh
python3 output_meter.py demo --lang fr
python3 output_meter.py context-demo --lang fr
```

## Ce que cet outil vérifie

Lit les entrées Codex JSONL `custom_tool_call_output` et `function_call_output`. Rapporte tailles, hachages SHA-256 répétés et marqueurs de troncation en local.

## Utiliser avec vos données

```sh
python3 output_meter.py report /path/to/rollout.jsonl --lang fr --json
```

Lancez `report` sur un journal Codex que vous possédez. L’outil affiche nombres et noms d’outils, jamais les sorties ; `--json` omet aussi leur contenu.

## Repérer le contexte injecté plusieurs fois

Dans DeepSeek Harness Web, choisissez **Download session log** ou `/export`, puis lancez :

```sh
python3 output_meter.py context /chemin/vers/dsh-session.zip --lang fr
python3 output_meter.py context /chemin/vers/session.v4.jsonl --lang fr --json
```

La commande lit le journal JSONL de la session racine dans l'export ZIP officiel ou dans un JSONL extrait. Par défaut, elle sélectionne les événements `user/message` non humains dont `source.kind` contient `hindsight`. `--kind ''` inclut toutes les sources injectées. Elle compte les blocs ajoutés identiques ou similaires à au moins 97 % pour une même source ; les remplacements et les événements sans ajout confirmé ne gonflent pas le total redondant. Elle n'affiche jamais le texte. La démo est synthétique. Nous avons contrôlé le parseur sur [un journal V4 public de DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness/blob/master/snapshots/web/permission-policy-context/session.v4.jsonl) avec `--kind ''`, mais **pas sur la session de l'auteur de l'issue Hindsight**.

## Périmètre et limites

`caractères/4` est une estimation grossière, sans lien direct avec la facturation. Le hachage détecte des sorties identiques, pas des répétitions sémantiques. Les chemins peuvent rester privés : gardez le rapport en local.

Pour le contexte injecté, les caractères redondants ne comptent que les messages ajoutés en plus. Ils ne mesurent pas les tokens d'entrée cumulés après rejeu et ne prouvent pas qu'un ancien contenu reste visible après compression. La commande lit les ZIP exportés ou les JSONL simples, pas les fichiers `.zstd` compressés directement.

## Tests

```sh
python3 -m unittest discover -s tests -v
```

MIT · v0.1.0-alpha.1
