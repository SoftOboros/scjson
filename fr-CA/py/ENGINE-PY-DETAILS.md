```markdown
<p align="center"><img src="../scjson.png" alt="scjson logo" width="200"/></p>

Nom de l'agent : python-engine-reference

Fait partie du projet scjson.
Développé par Softoboros Technology Inc.
Sous licence BSD 1-Clause.

# Paquet Python — Architecture et Référence

Ce document fournit une référence pratique et approfondie pour le paquet Python `scjson` : ses modules, comportements d'exécution, outils CLI et comment ils s'assemblent. Si vous souhaitez une utilisation rapide, consultez le résumé ci-dessous ; pour une exploration plus approfondie, passez aux sections liées.

Résumé rapide
- Aperçu CLI : scjson CLI prend en charge la conversion SCXML↔SCJSON, l'exportation de schémas, le traçage et la vérification du moteur. Voir : [CLI](#cli)
- Moteur d'exécution : runtime en un seul fichier avec évaluation d'expressions sécurisée, sémantique d'historique/parallèle, timers et invocation. Voir : [Moteur d'exécution](#execution-engine)
- Traçage et comparaison : traces JSONL déterministes, normalisation et comparaison de référence [SCION](https://www.npmjs.com/package/scion). Voir : [Comparaison de traces](#trace-compare)
- Génération de vecteurs et balayage : générer des vecteurs d'événements, mesurer la couverture et balayer les corpus. Voir : [Vecteurs et balayage](#vectors--sweep)
- Packaging : scripts console et modules installés par le paquet Python. Voir : [Packaging et scripts](#packaging--scripts)

Documents connexes
- docs/ENGINE-PY.md — guide d'utilisation du moteur et de la CLI
- docs/COMPATIBILITY.md — compatibilité inter-langues et notes de parité [SCION](https://www.npmjs.com/package/scion)
- codex/CONTEXT.md — contexte de session actuel et commandes de reproduction
- codex/CONTEXT-EXPANDED.md — instantané du contexte étendu

## Navigation

- Cette page : Architecture et Référence
  - [Disposition du paquet](#package-layout)
  - [Moteur d'exécution](#execution-engine)
  - [Évaluation sécurisée d'expressions](#safe-expression-evaluation)
  - [Convertisseur](#converter-scxml--scjson)
  - [CLI](#cli)
  - [Sous-système d'invocation](#invoke-subsystem)
  - [Minuteurs](#timers)
  - [Comparaison de traces](#trace-compare)
  - [Vecteurs et balayage](#vectors--sweep)
  - [Packaging et scripts](#packaging--scripts)
  - [Commandes de test et de reproduction](#testing--repro-commands)
- Guide de l'utilisateur : `docs/ENGINE-PY.md`
- Matrice de compatibilité : `docs/COMPATIBILITY.md`

---

## Disposition du paquet

Modules principaux du paquet (répertoire : `py/scjson`) :
- `cli.py` — interface en ligne de commande (conversion ; engine-trace/verify ; codegen).
- `context.py` — moteur d'exécution (macro/micro-étape, transitions, historique, invocation, timers, sémantique d'erreur, traçage).
- `events.py` — primitives `Event` et `EventQueue`.
- `activation.py` — enregistrements d'activation et spécifications de transition utilisés par le moteur.
- `safe_eval.py` — évaluation d'expressions en sandbox (par défaut) avec l'override `--unsafe-eval`.
- `invoke.py` — registre d'invocateurs léger et gestionnaire d'enfants SCXML/SCJSON.
- `SCXMLDocumentHandler.py` — convertisseur XML↔JSON utilisant xsdata/xmlschema.
- `json_stream.py` — décoder les flux JSONL sans dépendre du cadrage de nouvelle ligne.
- `jinja_gen.py` + templates — aides à la génération de code/schéma pour la CLI.

Outils de haut niveau (répertoire : `py/`) :
- `exec_compare.py` — exécute un graphique avec le moteur Python et compare avec une référence ([SCION](https://www.npmjs.com/package/scion) par défaut) ; diff JSONL avec normalisation.
- `exec_sweep.py` — balaye un répertoire de graphiques ; génération de vecteurs optionnelle ; agrège les résultats.
- `vector_gen.py` — génère des vecteurs d'événements et des sidecars de couverture.
- `vector_lib/` — analyseur/recherche/aides à la couverture pour la génération de vecteurs.

---

## Moteur d'exécution

Fichier : `py/scjson/context.py`

Concepts clés
- Activations et configuration : Un `ActivationRecord` représente un nœud actif (état/parallèle/final/historique). `configuration` est l'ensemble des ID d'activation actifs ; il se met à jour pendant les micro-étapes de transition.
- Macro/micro-étape : `microstep()` traite au plus un événement externe (plus tout traitement `done.invoke*` immédiatement pertinent) ; les transitions sans événement s'exécutent jusqu'à l'état de repos. `run()` boucle `microstep()` jusqu'à ce que la file d'attente se vide ou qu'un budget d'étapes soit atteint.
- Sélection de transition : `_select_transition(evt)` itère l'ordre du document, prend en charge les événements multi-tokens (séparés par des espaces), le caractère générique `*` et les motifs de préfixe `error.*`. `_eval_condition` s'exécute dans un bac à sable ; les résultats non booléens produisent `error.execution` et évaluent à faux.
- Entrée/Sortie/Historique : `_enter_state`, `_exit_state`, `_enter_history` gèrent l'ordre d'entrée/sortie basé sur LCA, la restauration de l'historique peu profond et profond, et la propagation `done.state.*`.
- Contenu exécutable : `assign`, `log`, `raise`, `if/elseif/else`, `foreach`, `send`, `cancel` et `script` (avertissement/no-op). L'ordre d'exécution des actions est préservé via l'ordre enfant XML ou la synthèse d'ordre JSON.
- Minuteurs : `_schedule_event` et `advance_time(seconds)` implémentent des minuteurs déterministes ; le traceur/CLI prend en charge l'injection de jetons de contrôle `{ "advance_time": N }` pour libérer les envois retardés entre les stimuli.
- Erreurs : `_emit_error` met en file d'attente `error.execution` (push-front) pour les échecs d'évaluation et `error.communication` pour les envois externes non pris en charge ou les échecs de chargement d'invocation. Un alias générique `error` est également émis pour `error.execution` afin de prendre en charge les graphiques écoutant `error.*`.
- Invocation : `_start_invocations_for_state`, `_on_invoke_done`, `_cancel_invocations_for_state` gèrent le cycle de vie de l'invocation ; la finalisation s'exécute dans l'état invoquant avec `_event` mappé ; interaction parent↔enfant via `#_parent`, `#_child`/`#_invokedChild` et `#_<invokeId>`.
- Modes d'ordonnancement : `ctx.ordering_mode` contrôle la priorité d'émission enfant→parent et la mise en file d'attente `done.invoke`.
  - tolérant (par défaut) : les émissions enfant sont push-front ; `done.invoke` est push-front uniquement si aucune sortie enfant ne la précède.
  - strict : les émissions enfant et `done.invoke` sont mises en file d'attente à la fin.
  - scion : les émissions enfant sont mises en file d'attente à la fin ; `done.invoke` est push-front avec le générique avant l'ID spécifique, correspondant à l'ordonnancement micro-étape observable de [SCION](https://www.npmjs.com/package/scion).

Aides notables
- Expressions sécurisées : `_evaluate_expr()` délègue à `safe_eval` sauf si `allow_unsafe_eval=True`.
- Entrée de trace : `trace_step(evt: Event|None)` renvoie un dictionnaire normalisé avec les clés : `event`, `firedTransitions`, `enteredStates`, `exitedStates`, `configuration`, `actionLog`, `datamodelDelta`.

---

## Évaluation sécurisée d'expressions

Fichier : `py/scjson/safe_eval.py`

- Bac à sable par défaut : Le moteur évalue les expressions via un bac à sable (`py-sandboxed`) en liste blanche qui bloque les importations, l'accès aux dunder et les builtins non sécurisés. Un ensemble sélectionné de builtins purs (et éventuellement `math.*`) sont exposés.
- Contrôles CLI : `engine-trace` accepte `--unsafe-eval` pour contourner le bac à sable (graphiques de confiance uniquement) ; les motifs d'autorisation/interdiction et les préréglages peuvent affiner l'exposition lorsqu'ils sont en bac à sable.
- Surface d'importation : préfère `py_sandboxed` (votre paquet géré) ; se rabat sur `py_sandboxer` pour les environnements qui exposent la même API sous un nom différent.
- Sémantique d'erreur : les violations de bac à sable ou les exceptions d'exécution lèvent `SafeEvaluationError` ; le moteur met en file d'attente `error.execution` et traite la condition comme fausse ou la valeur de l'expression comme un littéral le cas échéant.

---

## Convertisseur (SCXML ↔ SCJSON)

Fichier : `py/scjson/SCXMLDocumentHandler.py`

- Analyse/sérialisation : utilise `XmlParser`/`XmlSerializer` de xsdata et la validation `xmlschema` optionnelle.
- Strict vs lax : `fail_on_unknown_properties=True` applique une analyse XML stricte ; définissez `False` pour tolérer les éléments inconnus dans les graphiques non canoniques.
- Normalisation JSON : décimales/énumérations normalisées ; conteneurs vides supprimés par défaut ; balisage texte/imbriqué dans `<content>` conservé dans une structure JSON compatible [SCION](https://www.npmjs.com/package/scion).

---

## CLI

Fichier : `py/scjson/cli.py`

Commandes
- Conversion
  - `scjson json PATH [--output/-o OUT] [--recursive/-r] [--verify/-v] [--keep-empty] [--fail-unknown/--skip-unknown]`
  - `scjson xml PATH [--output/-o OUT] [--recursive/-r] [--verify/-v] [--keep-empty]`
- Validation
  - `scjson validate PATH [--recursive/-r]` (aller-retour en mémoire)
- Moteur
  - `scjson engine-trace -I CHART [--xml] [-e EVENTS] [--out OUT] [--lax/--strict] [--advance-time N] [--leaf-only] [--omit-actions] [--omit-delta] [--omit-transitions] [--ordering MODE] [--unsafe-eval|--expr-*]`
  - `scjson engine-verify -I CHART [--xml] [--advance-time N] [--max-steps N] [--lax/--strict]`
- Codegen et schéma
  - `scjson typescript -o OUT` / `scjson rust -o OUT` / `scjson swift -o OUT` / `scjson ruby -o OUT`
  - `scjson schema -o OUT` (écrit `scjson.schema.json`)

Options de trace
- Mode feuille uniquement, omettre action/delta/transitions, et `--advance-time` pour vider les minuteurs de manière déterministe avant de traiter les événements.

---

## Sous-système d'invocation

Fichier : `py/scjson/invoke.py`

- Registre et gestionnaires : `InvokeRegistry` avec des gestionnaires factices (`mock:immediate`, `mock:record`, `mock:deferred`) et des gestionnaires de machines enfants pour `scxml`/`scjson`.
- Machines enfants : Construites via `DocumentContext._from_model` avec une entrée initiale différée afin que les envois onentry puissent remonter avant que le parent ne voie `done.invoke`.
- E/S parent↔enfant : L'enfant émet avec les métadonnées d'E/S d'événement SCXML (`origintype`, `invokeid`) et prend en charge les envois `#_parent` ; le parent peut s'adresser à l'enfant par `#_child`/`#_invokedChild` ou `#_<invokeId>`.
- Sémantique de finalisation : `<finalize>` s'exécute dans l'état invoquant ; `_event` contient `{name, data, invokeid}`.

---

## Minuteurs

- Ordonnancement : `<send delay|delayexpr>` est ordonnancé par rapport à l'horloge simulée du moteur (`_timer_now`).
- Contrôle : `advance_time(seconds)` libère les minuteurs prêts ; la CLI accepte `--advance-time N` et les jetons de contrôle `{ "advance_time": N }` dans les flux d'événements.

---

## Comparaison de traces

Fichier : `py/exec_compare.py`

- Objectif : exécuter le moteur Python vs référence ([SCION](https://www.npmjs.com/package/scion) Node par défaut) et comparer les traces JSONL.
- Normalisation : filtrage feuille uniquement ; suppression du bruit de l'étape 0 (`datamodelDelta`, `firedTransitions`), suppression facultative des entrées/sorties de l'étape 0 ; clés `datamodelDelta` triées.
- Référence : se résout automatiquement à `tools/scion-runner/scion-trace.cjs` si disponible (ou remplace `SCJSON_REF_ENGINE_CMD`).
- Vecteurs : peut générer des vecteurs à la volée (`--generate-vectors`) et adopter `advanceTime` recommandé des métadonnées du vecteur.

---

## Vecteurs et balayage

Fichier : `py/vector_gen.py`, aides dans `py/vector_lib/`

- Analyseur : extrait un alphabet d'événements des transitions et des indices d'invocation simples ; heuristiques de charge utile des expressions `cond`.
- Recherche : BFS guidée par la couverture sur l'alphabet (`vector_lib.search.generate_sequences`) ; prend en charge les stimuli porteurs de données.
- Génération : écrit `.events.jsonl`, `.coverage.json` et `.vector.json` (métadonnées avec `advanceTime`). Ajoute `{ "advance_time": N }` entre les stimuli lorsque des minuteurs sont en attente.
- Balayage : `py/exec_sweep.py` découvre les graphiques, génère des vecteurs s'ils manquent, compare les traces et agrège la couverture.

---

## Packaging et scripts

Fichier : `py/pyproject.toml`

- Version : `0.3.5`
- Dépendances : `pydantic`, `lxml`, `jsonschema`, `click`, `py-sandboxed` (bac à sable), `jinja2`, `xmlschema`, `xsdata`.
- Scripts console :
  - `scjson` — CLI principale
  - `scjson-exec-compare` — comparer les traces par rapport à la référence
  - `scjson-exec-sweep` — balayer les répertoires avec génération de vecteurs optionnelle
  - `scjson-vector-gen` — générateur de vecteurs autonome
- Modules installés : `exec_compare`, `exec_sweep`, `vector_gen`

---

## Commandes de test et de reproduction

- Tests unitaires : `PYTHONPATH=py pytest -q py/tests`
- Vérifications rapides du moteur (SCXML) :
  - `PYTHONPATH=py python -m scjson.cli engine-verify -I tutorial/.../test253.scxml --xml --advance-time 3`
  - Répéter pour : 338, 422, 554 → succès attendu
  - `test401.scxml` (précédence des erreurs) passe sans `--advance-time`
- Comparaison de traces : `python py/exec_compare.py <chart.scxml> --events <events.jsonl>`
- Génération de vecteurs : `python py/vector_gen.py <chart.scxml> --xml --out vectors/`

---

## Limitations connues et notes de compatibilité

- Processeurs externes : Les cibles `<send>` externes (autres que `#_parent`, `_internal`) ne sont pas exécutées ; le moteur émet `error.communication` et ignore la livraison.
- Visibilité de l'étape 0 : Les moteurs diffèrent sur les transitions initiales ; la normalisation atténue les différences.
- Ordre d'invocation : Le mode `scion` aligne la mise en file d'attente `done.invoke` avec [SCION](https://www.npmjs.com/package/scion) ; les modes `tolerant/strict` offrent des alternatives flexibles.

---

## Annexe : Schéma de trace (Étapes du moteur)

Chaque étape produite par `trace_step` ou `engine-trace` comprend :
- `event` : `{name, data}` de l'événement externe consommé (ou `null` pour l'étape 0)
- `firedTransitions` : `[{source, targets[], event, cond}]` filtré aux états utilisateur
- `enteredStates` / `exitedStates` : listes d'ID d'état (filtrées par feuille si demandé)
- `configuration` : ID d'état actifs actuels (filtrés par feuille si demandé)
- `actionLog` : entrées de `log`, éventuellement omises
- `datamodelDelta` : clés modifiées depuis l'étape précédente, avec clés triées (éventuellement omises)

---

## Annexe : Glossaire

- Activation : Un enregistrement d'exécution d'un nœud SCXML entré (état/parallèle/final/historique).
- Configuration : L'ensemble des ID d'activation actuellement actifs.
- Macro-étape : Une `microstep()` plus l'épuisement des transitions sans événement jusqu'à l'état de repos.
- [SCION](https://www.npmjs.com/package/scion) : Moteur SCXML de référence utilisé pour la comparaison des comportements.

---

Retour à
- Guide de l'utilisateur : `docs/ENGINE-PY.md`
- Matrice de compatibilité : `docs/COMPATIBILITY.md`
```
