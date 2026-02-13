Ce guide explique comment utiliser l'interface du moteur d'exécution Ruby pour émettre des traces JSONL déterministes et comment comparer le comportement avec le moteur de référence ([SCION](https://www.npmjs.com/package/scion)) et le moteur Python. Il reflète le guide Python, le cas échéant, tout en respectant les conventions Ruby.

Vous cherchez des détails d'implémentation plus approfondis? Voir la référence architecturale dans `ruby/ENGINE-RB-DETAILS.md`.

Pour les détails sur la parité inter-langues et la comparaison SCION, voir `docs/COMPATIBILITY.md`.

## Navigation

- Cette page: Guide de l'utilisateur
  - Aperçu
  - Démarrage rapide
  - Flux d'événements (.events.jsonl)
- Architecture et référence approfondie: `ruby/ENGINE-RB-DETAILS.md`
- Matrice de compatibilité: `docs/COMPATIBILITY.md`

## Aperçu

L'interface du moteur Ruby est en cours de développement pour exécuter des automates SCXML/SCJSON et émettre des traces JSONL déterministes d'exécution. Un ensemble d'utilitaires CLI et le harnais Python existant vous aident à:

- Exécuter le moteur Ruby et collecter des traces
- Comparer les traces Ruby avec un moteur de référence (SCION/Node) et Python
- Réutiliser les vecteurs d'événements existants et les jetons de contrôle pour des exécutions déterministes

Composants clés (chemins relatifs à la racine du dépôt):

- `ruby/lib/scjson/cli.rb` – CLI Ruby, y compris `engine-trace`
- `ruby/lib/scjson/engine.rb` – interface de trace du moteur (ébauche; s'étend avec le temps)
  - Drapeaux de normalisation: `--leaf-only`, `--omit-actions`, `--omit-delta`, `--omit-transitions`, `--strip-step0-noise`, `--strip-step0-states`, `--keep-cond`
  - Ordre: `--ordering tolerant|strict|scion` (affecte l'ordre des événements done.invoke)
- `py/exec_compare.py` – compare les traces avec la référence et un secondaire optionnel (à utiliser pour Ruby)

Les traces sont des objets JSON délimités par des lignes avec les champs: `event`, `firedTransitions`, `enteredStates`, `exitedStates`, `configuration`, `actionLog`, `datamodelDelta`, `step`.

## Démarrage rapide

1) Trace du moteur (Ruby; entrée SCXML)

```bash
ruby/bin/scjson engine-trace -I tests/exec/toggle.scxml \
  -e tests/exec/toggle.events.jsonl -o toggle.ruby.trace.jsonl --xml \
  --leaf-only --omit-delta --strip-step0-noise --strip-step0-states
```

Remarques:
- `-I` pointe vers le graphique d'entrée; ajoutez `--xml` pour l'entrée SCXML, omettez pour SCJSON.
- `-e` fournit un fichier d'événements JSONL (voir "Flux d'événements").
- Les drapeaux de normalisation réduisent le bruit et maintiennent les traces déterministes.

2) Comparer avec le moteur de référence avec Ruby comme secondaire

```bash
python py/exec_compare.py tests/exec/toggle.scxml \
  --events tests/exec/toggle.events.jsonl \
  --reference "node tools/scion-runner/scion-trace.cjs" \
  --secondary "ruby/bin/scjson engine-trace" \
  --leaf-only --omit-delta
```

3) Balayer un répertoire de graphiques (Ruby comme secondaire)

```bash
python py/exec_sweep.py tutorial \
  --glob "**/*.scxml" \
  --reference "node tools/scion-runner/scion-trace.cjs" \
  --workdir uber_out/sweep \
  --secondary "ruby/bin/scjson engine-trace"
```

Lors de l'utilisation de vecteurs générés, le harnais Python écrit un `coverage-summary.json` avec la couverture agrégée des graphiques.

## Flux d'événements (.events.jsonl)

Les flux d'événements sont des objets JSON délimités par des retours à la ligne, un par événement:

```json
{"event": "start"}
{"event": "go", "data": {"flag": true}}
```

Clés acceptées:
- `event` (ou `name`) – nom de l'événement sous forme de chaîne
- `data` – charge utile optionnelle (objet, nombre, chaîne, etc.)

Jetons de contrôle:
- `advance_time` – nombre de secondes à avancer l'horloge du moteur avant que l'événement externe suivant ne soit traité. Aucune étape de trace n'est émise pour ce jeton de contrôle. Cela reflète le comportement de Python pour maintenir les traces comparables.
  - La CLI Ruby prend également en charge `--advance-time N` pour appliquer une avance de temps initiale avant le premier événement.

## Notes CI — Retour en arrière du convertisseur

- Le convertisseur SCXML↔scjson de Ruby utilise Nokogiri lorsqu'il est disponible. Certains environnements CI n'installent pas les gems Ruby (Nokogiri nécessite des extensions natives). Pour que le harnais du moteur reste utilisable dans ces environnements, le convertisseur Ruby se rabat de manière transparente sur la CLI Python pour la conversion:
  - SCXML→scjson: `python -m scjson.cli json <in.scxml> -o <out.scjson>`
  - scjson→SCXML: `python -m scjson.cli xml <in.scjson> -o <out.scxml>`
- Ce retour en arrière ne concerne que la conversion de format de fichier; l'exécution/traçage est toujours effectuée par le moteur Ruby. L'utilisation du convertisseur Python maintient le JSON canonique identique entre les langues et évite la variance spécifique au CI.
- Si vous préférez, convertissez les graphiques à l'avance et exécutez le moteur Ruby sur les entrées scjson pour contourner entièrement l'analyse XML:
  - `python -m scjson.cli json chart.scxml -o chart.scjson`
  - `ruby/bin/scjson engine-trace -I chart.scjson -e chart.events.jsonl`

Couverture de la documentation
- Les vérifications de conversion et de construction de la documentation sont exécutées plus tôt dans le pipeline CI; au moment où le harnais du moteur Ruby s'exécute, les documents et les convertisseurs ont déjà été validés. Le retour en arrière de Nokogiri supprime simplement le besoin d'une pile XML native Ruby dans les étapes ultérieures.

## Dépannage

- Différences connues dans les exécutions CI
  - Certains graphiques présentent des différences intentionnelles et documentées entre les moteurs (par exemple, la sémantique `in` d'ECMA, les nuances de réentrée de l'historique). Utilisez la liste des différences connues pour maintenir le CI vert tout en signalant ces cas:
    - Fichier: `scripts/ci_ruby_known_diffs.txt`
    - Harnais: `bash scripts/ci_ruby_harness.sh --list scripts/ci_ruby_charts.txt --known scripts/ci_ruby_known_diffs.txt`

- Profil de normalisation pour les comparaisons
  - Utilisez le profil SCION pour aligner les champs de sortie et l'ordre entre les moteurs:
    - `python py/exec_compare.py <graphique> --events <événements> --reference "node tools/scion-runner/scion-trace.cjs" --norm scion`
  - `--norm scion` définit: feuille seulement, omettre le delta, omettre les transitions, supprimer les états de l'étape 0 et ordre=scion.

- Pré-convertir SCXML en scjson pour l'exécution Ruby
  - Pour éviter les différences d'analyseur XML ou la configuration de Nokogiri sur votre machine, pré-convertissez une fois et exécutez Ruby sur scjson:
    - `python -m scjson.cli json chart.scxml -o chart.scjson`
    - `ruby/bin/scjson engine-trace -I chart.scjson -e chart.events.jsonl`

- Dépendance Nokogiri (développement local)
  - Le convertisseur SCXML↔scjson de Ruby utilise la gem Nokogiri pour l'analyse XML lorsqu'il est exécuté à partir de la source. Si la gem n'est pas installée, la CLI Ruby se rabat de manière transparente sur le convertisseur Python (voir "Notes CI").
  - Pour une meilleure performance locale et pour tout garder en Ruby, installez Nokogiri (et les dépendances de construction système) dans votre environnement. Sinon, le retour en arrière Python sera utilisé pour la conversion tandis que l'exécution restera en Ruby.

---

Retour à
- Architecture et référence: `ruby/ENGINE-RB-DETAILS.md`
- Matrice de compatibilité: `docs/COMPATIBILITY.md`
- Aperçu du projet: `README.md`
