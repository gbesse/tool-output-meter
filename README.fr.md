# Tool Output Meter

**Pourquoi mon agent a-t-il oublié ?** Voyez quels souvenirs arrivent à chaque tour, quels faits stockés n'ont pas de lien vers une observation et quand un document accepté devient lisible. Mesurez aussi les sorties d'outils répétées sans afficher leur contenu.

[English](README.md) · [Français](README.fr.md) · [Español](README.es.md)

## Projets voisins

- [Codex issue #40897](https://github.com/openai/codex/issues/40897) — Documente un cas concret de sorties trop volumineuses.
- [compress](https://github.com/spenmcke/compress) — Réduit les sorties via un service distant ; ce dépôt mesure seulement des journaux locaux.
- [Codex](https://github.com/openai/codex) — Produit les enregistrements JSONL lus par le parseur.
- [Hindsight #5026](https://github.com/vectorize-io/hindsight/issues/5026) — Signale un contexte presque identique injecté à chaque tour de DeepSeek Harness.
- [Hindsight #5082](https://github.com/vectorize-io/hindsight/issues/5082) — Décrit des tours avec consignes statiques mais sans souvenir utile ; la nouvelle commande classe ce format connu.
- [Hindsight #5054](https://github.com/vectorize-io/hindsight/issues/5054) — Décrit des faits marqués consolidés sans liens d'observation ; `coverage.py` contrôle cette forme exportée.
- [Hindsight #5077](https://github.com/vectorize-io/hindsight/issues/5077) — Décrit des écritures acceptées mais visibles bien plus tard ; `receipt.py` interroge une URL de lecture fournie.
- [Hindsight #5073](https://github.com/vectorize-io/hindsight/issues/5073) et [Hermes Agent](https://github.com/NousResearch/hermes-agent) — Motivent l'audit des tags de sujet ; `router.py` n'est pas une intégration Hermes en direct.
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

## Un vrai souvenir est-il arrivé ?

```sh
python3 output_meter.py memory-demo --lang fr
python3 output_meter.py memory /chemin/vers/dsh-session.zip --lang fr --json
python3 output_meter.py memory /chemin/vers/dsh-session.zip --lang fr --html /tmp/memory-xray.html
```

Le rapport local compte les tours avec souvenir confirmé, mémoire vide, format inconnu ou absence d'injection Hindsight. Il reconnaît uniquement le format `hindsight_memory` de Hindsight coding-agents 0.8.0 ; un format modifié reste inconnu. La démo est synthétique. L'arrivée ne prouve pas l'utilisation du souvenir, et cette commande ne lit pas la banque stockée.

La vue HTML **Memory X-Ray** est une chronologie locale autonome. Elle montre uniquement les numéros de tours et leur classe, jamais le texte des souvenirs. Ouvrez le fichier produit dans votre navigateur. C'est une vue de Tool Output Meter, pas une intégration ou un dépôt séparé.

## Contrôler les autres pertes de mémoire

```sh
python3 coverage.py demo --lang fr
python3 coverage.py check facts.json observations.json --lang fr
python3 receipt.py demo --lang fr
python3 receipt.py watch https://localhost:8888/documents/DOC_ID --lang fr
python3 router.py demo --lang fr
python3 router.py audit --event fixtures/event.json --records fixtures/records.json --lang fr
```

`coverage.py` lit les JSON de faits et d'observations exportés d'une banque que vous contrôlez ; un fait marqué sans lien est une lacune **possible**. Il refuse les observations sans `source_memory_ids`. `receipt.py` lance uniquement des GET vers l'URL exacte fournie et distingue un 404 tardif d'un 403 ; un jeton facultatif vient de `--token-env VARIABLE` et n'est jamais affiché. `router.py` produit des tags pseudonymes stables à partir d'un chat et d'un sujet Telegram, puis contrôle un export local. Il ne configure **pas** le rappel automatique de Hermes et ses hachages ne sont pas une barrière d'accès. Ces commandes permettent de passer de l'injection à la couverture stockée, à la visibilité tardive et à la séparation des sujets. Leurs démos sont synthétiques ; seule la commande GET contacte une URL fournie par l'utilisateur.

## Périmètre et limites

`caractères/4` est une estimation grossière, sans lien direct avec la facturation. Le hachage détecte des sorties identiques, pas des répétitions sémantiques. Les chemins peuvent rester privés : gardez le rapport en local.

Pour le contexte injecté, les caractères redondants ne comptent que les messages ajoutés en plus. Ils ne mesurent pas les tokens d'entrée cumulés après rejeu et ne prouvent pas qu'un ancien contenu reste visible après compression. La commande lit les ZIP exportés ou les JSONL simples, pas les fichiers `.zstd` compressés directement.

## Tests

```sh
python3 -m unittest discover -s tests -v
```

MIT · v0.1.2-alpha.1
