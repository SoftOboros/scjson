```markdown
<p align="center"><img src="../scjson.png" alt="scjson logo" width="200"/></p>

# Moteur Python — Guide de l'utilisateur

Ce guide explique comment utiliser le moteur d'exécution Python et les outils complémentaires pour tracer des graphiques, les comparer à un moteur de référence, générer des vecteurs de test et balayer des corpus. Il s'agit d'un complément orienté utilisateur à la liste de contrôle de développement dans `docs/TODO-ENGINE-PY.md`.

Vous cherchez des détails d'implémentation plus approfondis ? Consultez la référence d'architecture à `py/ENGINE-PY-DETAILS.md`.

Pour les détails de parité inter-langues et de comparaison [SCION](https://www.npmjs.com/package/scion), consultez `docs/COMPATIBILITY.md`.

## Navigation

- Cette page : Guide de l'utilisateur
  - [Aperçu](#aperçu)
  - [Démarrage rapide](#démarrage-rapide)
  - [Flux d'événements](#flux-dévénements-eventsjsonl)
- [Génération de vecteurs](#génération-de-vecteurs)
  - [Contrôle du temps](#contrôle-du-temps)
- Architecture et référence approfondie : `py/ENGINE-PY-DETAILS.md`
- Matrice de compatibilité : `docs/COMPATIBILITY.md`

## Aperçu

Le moteur Python exécute les statecharts SCXML/SCJSON et peut émettre des traces d'exécution JSONL déterministes. Un ensemble d'utilitaires CLI vous aide à :

- Exécuter le moteur Python et collecter des traces
- Comparer les traces Python à un moteur de référence ([SCION](https://www.npmjs.com/package/scion)/Node)
- Générer des vecteurs d'événements d'entrée pour améliorer la couverture
- Balayer des dossiers de graphiques, générer automatiquement des vecteurs et agréger la couverture

Composants clés (chemins relatifs à la racine du dépôt) :

- `py/scjson/cli.py` – CLI principale, y compris `engine-trace`
- `py/exec_compare.py` – Comparer Python au moteur de référence (et secondaire facultatif)
- `py/exec_sweep.py` – Balayer un répertoire et comparer tous les graphiques
- `py/vector_gen.py` – Générateur de vecteurs d'événements avec heuristiques de couverture

Les traces sont des objets JSON délimités par des lignes avec les champs : `event`, `firedTransitions`, `enteredStates`, `exitedStates`, `configuration`, `actionLog`, `datamodelDelta`.

## Démarrage rapide

1) Trace du moteur (Python uniquement)

```bash
python -m scjson.cli engine-trace -I tests/exec/toggle.scxml \
  -e tests/exec/toggle.events.jsonl -o toggle.python.trace.jsonl --xml \
  --leaf-only --omit-delta
```

Notes :
- `-I` pointe vers le graphique d'entrée ; ajoutez `--xml` pour l'entrée SCXML, omettez pour SCJSON.
- `-e` fournit un fichier d'événements JSONL (voir « Flux d'événements »).
- Les drapeaux de normalisation réduisent le bruit et maintiennent les traces déterministes.

2) Comparer au moteur de référence

```bash
python py/exec_compare.py tests/exec/toggle.scxml \
  --events tests/exec/toggle.events.jsonl \
  --reference "node tools/scion-runner/scion-trace.cjs" \
  --leaf-only --omit-delta
```

Si vous omettez `--events`, vous pouvez demander à l'outil de générer des vecteurs :

```bash
python py/exec_compare.py tests/exec/toggle.scxml \
  --generate-vectors --gen-depth 2 --gen-variants-per-event 3
```

3) Balayer un répertoire de graphiques

```bash
python py/exec_sweep.py tutorial \
  --glob "**/*.scxml" \
  --reference "node tools/scion-runner/scion-trace.cjs" \
  --generate-vectors --gen-depth 2 --gen-variants-per-event 3 \
  --workdir uber_out/sweep
```

Lorsque `--workdir` est fourni et que les vecteurs sont générés, un `coverage-summary.json` est écrit avec la couverture agrégée sur tous les graphiques.

---

Retour à
- Architecture et référence : `py/ENGINE-PY-DETAILS.md`
- Matrice de compatibilité : `docs/COMPATIBILITY.md`

## Flux d'événements (.events.jsonl)

Les flux d'événements sont des objets JSON délimités par des retours à la ligne, un par événement :

```json
{"event": "start"}
{"event": "go", "data": {"flag": true}}
```

Clés acceptées :
- `event` (ou `name`) – nom d'événement chaîne de caractères
- `data` – charge utile facultative (objet, nombre, chaîne de caractères, etc.)

Jetons de contrôle :
- `advance_time` – nombre de secondes pour avancer l'horloge simulée du moteur Python avant que le prochain événement externe ne soit traité. Ceci est ignoré par les moteurs de référence qui ne consomment que `event`/`name`, mais permet au moteur Python de vider les temporisateurs `<send>` retardés entre les stimuli pour mieux correspondre aux moteurs qui ne modélisent pas le temps explicitement.

## Contrôle du temps

Par défaut, la CLI émet une étape synthétique chaque fois qu'un jeton de contrôle `{"advance_time": N}` est traité afin que les temporisateurs dus soient visibles même si aucun événement externe ultérieur ne se produit. Désactivez ce comportement avec `--no-emit-time-steps` lorsque la parité stricte avec les outils qui n'émettent pas de telles étapes est souhaitée.

Exemple :

```bash
python -m scjson.cli engine-trace -I chart.scxml --xml \
  -e stream.events.jsonl --leaf-only --omit-delta
```

Notes :
- L'étape synthétique définit `event` à `null` et suit par ailleurs les mêmes règles de normalisation (`--leaf-only`, `--omit-*`).
- Utilisez `--no-emit-time-steps` pour supprimer ces étapes si vous comparez avec des outils qui ne les émettent pas.

## Génération de vecteurs

`py/vector_gen.py` génère des séquences d'événements compactes pour explorer le comportement d'un graphique. Il extrait un alphabet d'événements et utilise une recherche guidée par la couverture avec des heuristiques de charge utile.

Fonctionnalités principales :
- Extraction de l'alphabet à partir des jetons d'événement de transition (ignore les caractères génériques/motifs de préfixe)
- Heuristiques de charge utile à partir des expressions `cond` sur `_event.data.*` :
  - Valeur de vérité / négation (True/False)
  - Égalité/inégalité et seuils numériques
  - Tests d'appartenance (y compris les formes inversées et les conteneurs de modèles de données)
  - Plages numériques chaînées/divisées
- Fusion de charge utile :
  - Fusionne les indices non conflictuels par condition pour des charges utiles plus riches
  - Variantes de « basculement de branche » à un coup (positive pour une condition, négative pour les autres)
- Détection d'avance automatique : si le graphique planifie des envois retardés lors de l'initialisation, le générateur recommande et applique une petite avance de temps initiale

Utilisation de la CLI :

```bash
python py/vector_gen.py path/to/chart.scxml --xml \
  --out ./vectors --max-depth 2 --limit 1 \
  --variants-per-event 3 --advance-time 0 \
  # utilisez --no-auto-advance pour désactiver la détection d'envoi retardé
```

Sorties écrites à côté du nom de base du graphique :
- `<name>.events.jsonl` – séquence d'événements générée
- `<name>.coverage.json` – résumé de la couverture pour la séquence
- `<name>.vector.json` – métadonnées incluant `advanceTime`, `sequenceLength` et les comptes d'indices

`exec_compare` et `exec_sweep` adoptent le `advanceTime` recommandé à partir de `.vector.json` lorsque vous utilisez `--generate-vectors` et ne passez pas de `--advance-time` explicite.

Le nombre de variantes de charge utile candidates par événement est plafonné par `--variants-per-event`.

Injection d'avance de temps en milieu de séquence
- Lorsque le graphique planifie des événements `<send>` retardés après l'initialisation, le générateur injecte désormais des jetons de contrôle (`{"advance_time": N}`) entre les stimuli externes dans `<name>.events.jsonl` afin que ces temporisateurs soient libérés avant le prochain événement. La CLI `engine-trace` comprend ces jetons et avance l'horloge simulée de l'interprète sans émettre d'étape de trace ; le moteur de référence [SCION](https://www.npmjs.com/package/scion) les ignore (il ne regarde que `event`/`name`).

Ce comportement améliore la parité inter-moteurs lorsque la référence ne modélise pas le temps, tout en maintenant le format du flux d'événements rétrocompatible.

## Normalisation et drapeaux

Ces drapeaux apparaissent sur `engine-trace`, `exec_compare` et `exec_sweep` pour maintenir une sortie reproductible et concentrer les comparaisons :

- `--leaf-only` – restreint `configuration`, `enteredStates` et `exitedStates` aux états feuilles
- `--omit-delta` – efface `datamodelDelta` (l'étape 0 est toujours normalisée)
- `--omit-actions` – efface `actionLog`
- `--omit-transitions` – efface `firedTransitions`
- `--advance-time <seconds>` – avance le temps simulé avant le traitement des événements (et se propage aux invocations enfants)

Normalisation de l'étape 0 : les traces Python et de référence voient `datamodelDelta` et `firedTransitions` effacés à l'étape 0. Le filtrage des états feuilles réduit davantage la variance de l'étape 0.

## Moteur de référence ([SCION](https://www.npmjs.com/package/scion))

La référence par défaut est l'implémentation Node de [SCION](https://www.npmjs.com/package/scion) ; un script d'aide est inclus. `exec_compare` et `exec_sweep` l'utilisent automatiquement lorsqu'il est présent.

Configuration unique :

```bash
cd tools/scion-runner
npm install
```

Pointez `exec_compare`/`exec_sweep` explicitement avec :

```bash
--reference "node tools/scion-runner/scion-trace.cjs"
```

Alternativement, définissez `SCJSON_REF_ENGINE_CMD` dans votre environnement. Lorsque d'autres moteurs sont ajoutés, ils devraient par défaut se comparer à [SCION](https://www.npmjs.com/package/scion) comme référence.

## Exemples

Tracer et comparer avec des vecteurs générés :

```bash
python py/exec_compare.py tests/exec/toggle.scxml \
  --generate-vectors --gen-depth 2 --gen-variants-per-event 2 \
  --reference "node tools/scion-runner/scion-trace.cjs"
```

Balayer un dossier et écrire le résumé de la couverture :

```bash
python py/exec_sweep.py tutorial \
  --glob "**/*.scxml" --generate-vectors \
  --gen-depth 2 --gen-variants-per-event 3 \
  --workdir uber_out/sweep \
  --reference "node tools/scion-runner/scion-trace.cjs"
```

Générer des vecteurs uniquement (sans comparaison) :

```bash
python py/vector_gen.py examples/demo.scxml --xml \
  --out ./vectors --max-depth 2 --variants-per-event 3
```

## Couverture

La couverture est un simple agrégat d'éléments uniques :
- ID d'états entrés
- Transitions déclenchées (par source et cibles)
- Événements `done.*`
- Événements `error*`

`exec_sweep` agrège la couverture pour les vecteurs générés et écrit un `coverage-summary.json` lorsque `--workdir` est fourni. Les fichiers de couverture par graphique sont écrits par `vector_gen.py`.

## Dépannage

- Si `engine-trace` est indisponible, `exec_compare` utilise un exécuteur Python intégré.
- Pour les entrées SCXML qui planifient des envois retardés pendant l'initialisation, utilisez `--advance-time` (ou fiez-vous à la détection automatique du générateur) afin que ces temporisateurs soient vidés avant le premier événement externe.
- Si Node est indisponible, vous pouvez toujours exécuter `exec_sweep` en utilisant le moteur Python comme référence : `--reference "$(python -c 'import sys;print(sys.executable)') -m scjson.cli engine-trace"`.

## Plus de détails

Pour les notes de conception, l'état d'implémentation et les limitations connues, voir : `py/scjson/ENGINE.md` et `docs/TODO-ENGINE-PY.md`.
```
