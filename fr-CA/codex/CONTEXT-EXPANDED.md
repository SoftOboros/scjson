# Moteur Python - Aperçu du Contexte Élargi (2025-10-02)

Cet aperçu élargi est conçu pour accélérer la reprise après un redémarrage à froid. Il capture ce qui compte le plus actuellement : où se trouvent les choses, ce qui a changé, comment reproduire et ce qu'il faut faire ensuite.

## Reprise Rapide
- Exécuter les tests unitaires : `PYTHONPATH=py pytest -q py/tests`
- Activer explicitement le "slow smoke" : `PYTHONPATH=py pytest -q -m slow -k "uber_test and executes_chart"`
- "Smoke" paramétré (un test par graphique tutoriel) :
  - Tous : `PYTHONPATH=py pytest -q -k "uber_test and executes_chart"`
  - Filtrer par nom : `PYTHONPATH=py pytest -q -k "executes_chart and parallel_invoke_complete.scxml"`
- "Smoke" CLI avec sortie de progression :
  - Tous : `python py/uber_test.py --python-smoke`
  - Un seul graphique : `python py/uber_test.py --python-smoke --chart tutorial/Tests/python/W3C/Mandatory/Auto/test253.scxml`
- Vérifier les résultats W3C (faire avancer les minuteurs) :
  - `PYTHONPATH=py python -m scjson.cli engine-verify -I tutorial/Tests/python/W3C/Mandatory/Auto/test253.scxml --xml --advance-time 3`
  - Répéter pour 338, 422, 554 → attendu : succès
  - 401 (priorité d'erreur générique) : `--xml` (pas d'avance) → attendu : succès
- Comparer les traces avec la référence (feuille seulement + normalisation à l'étape 0) :
  - `python py/exec_compare.py <chart.scxml> --events <events.jsonl>`
  - Optionnel : `--keep-step0-states` pour préserver les états entrés/sortis à l'étape 0

## Pointeur de Dépôt (Quoi/Où)
- Cœur du moteur : `py/scjson/context.py`
  - Macro/Micro-étape, sélection de transition : `_select_transition`
  - Entrée/Sortie et Historique : `_enter_state`, `_exit_state`, `_enter_history`, `_handle_entered_final`
  - Contenu exécutable : `_run_actions`, `_iter_actions`, `_build_action_sequence`
  - Envoyer/Annuler : `_do_send`, `_do_cancel`, minuteurs : `_schedule_event`, `_release_delayed_events`, `advance_time`
  - Expressions et portée : `_scope_env`, `_evaluate_expr` (évaluation sécurisée par défaut)
  - Cycle de vie d'invocation : `_start_invocations_for_state`, `_start_invocations_for_active_states`, `_on_invoke_done`, `_cancel_invocations_for_state`
  - Aide à l'erreur : `_emit_error` (alias spécifique + générique pour `error.execution`)
- Sous-système d'invocation : `py/scjson/invoke.py` (mock:immediate, mock:record, mock:deferred, enfant scxml/scjson)
- Événements/file d'attente : `py/scjson/events.py` (`Event` inclut `origin`, `origintype`, `invokeid`)
- CLI : `py/scjson/cli.py` (`engine-trace`, `engine-verify`)
- Outil de comparaison de traces : `py/exec_compare.py`
- Wrapper de comparaison d'exécution pour les tests : `py/py/exec_compare.py`
- Conception/Docs : `py/scjson/ENGINE.md`, `docs/TODO-ENGINE-PY.md`
- Tutoriel/Corpus : `tutorial/` (W3C + exemples), liste d'exclusion : `py/uber_test.py::ENGINE_KNOWN_UNSUPPORTED`

## Aperçu Comportemental (Implémenté)
- Exécution + Structure
  - Boucle de macro-étape avec transitions sans événement jusqu'à la quiescence
  - Sélection déterministe de transition (ordre du document)
  - Ensembles d'entrée/sortie via LCA; le parallèle émet le "done" de la région et le "done" du parent
  - Historique peu profond et profond (le profond restaure les descendants exacts des feuilles)
  - Contenu exécutable : assigner, loguer, déclencher, if/elseif/else, foreach, envoyer (immédiat + retardé), annuler, script (no-op)
- Expressions et Erreurs
  - Évaluation sécurisée par défaut; `--unsafe-eval` optionnel
  - `error.execution` lorsque les expressions cond/foreach/assign échouent ou que cond n'est pas booléen (poussé en tête)
  - Alias générique `error` émis pour `error.execution` (pas pour `error.communication`) pour prendre en charge les graphiques écoutant `error.*`
  - Assignation à un emplacement invalide : met en file d'attente `error.execution` (pas de création de variable); alias priorisé pour l'ordre d'entrée
- Envois et Minuteurs
  - Interne : `#_internal`/`_internal` met en file d'attente dans la file d'attente du moteur
  - Externe : les cibles non prises en charge déclenchent `error.communication` et sont ignorées
  - Envois retardés déterministes : `advance_time(seconds)` libère dans l'ordre
  - Jetons de contrôle : `engine-trace` accepte des lignes de flux d'événements comme `{"advance_time": N}` pour faire avancer le temps sans émettre d'étape (utilisé par la génération de vecteurs)
- Invocation
  - Démarrage en fin de macro-étape pour les états entrés et non sortis pendant l'étape
  - Parent↔Enfant : #_parent bubbling; parent #_child/#_invokedChild et explicite #_<invokeId>
  - Renvoi automatique des événements externes aux invocations actives (ignore les annulées)
  - La finalisation s'exécute dans l'état d'invocation; les mappages `_event` incluent `name`, `data`, `invokeid`, `origin`/`origintype` facultatifs
  - Ordre des "done" : spécifique à l'ID puis générique par défaut, avec des préférences pour préserver l'ordre lorsque l'enfant émet pendant l'initialisation
  - L'échec du démarrage de l'enfant scxml/scjson génère `error.communication`
- Correspondance d'Événements
  - Listes d'événements séparées par des espaces
  - Caractère générique `*` et motifs de préfixe comme `error.*`

## Normalisation des Traces
- Comparaison "feuille seulement" (configuration/entré/sorti limité aux états feuilles)
- Suppression du bruit de l'étape 0 par défaut : `datamodelDelta` et `firedTransitions`
- Optionnel : supprimer `enteredStates`/`exitedStates` de l'étape 0, sauf si `--keep-step0-states` est fourni

## État Actuel
- Suite unitaire (Python) : verte → `PYTHONPATH=py pytest -q py/tests`
- Résultats rapides du jeu de tests obligatoires W3C (avec `--advance-time 3` le cas échéant) :
  - 253 : succès; 338 : succès; 422 : succès; 554 : succès
  - 401 : succès (priorité d'erreur générique via invalid-assign + alias)
- Graphiques "python-datamodel" tutoriels découverts : 208
- Échantillon ad hoc de 50 graphiques : aucun échec de construction d'une étape via `trace_step()`

## Diff (Depuis l'Aperçu Précédent)
- engine-trace : prend en charge les jetons de contrôle `{"advance_time": N}` dans les événements JSONL
- vector_gen : injecte des jetons `advance_time` en milieu de séquence lorsque des minuteurs sont en attente après une étape
- Ajout de `tests/sweep_corpus/*` sélectionnés et de tests exec_compare avancés
- Ajout d'un shim `py/py/exec_compare.py` pour la stabilité du chemin de test
- uber_test : tests paramétrés par graphique; mode "smoke" CLI avec progression par graphique
- Documentation mise à jour : jetons de contrôle, injection de vecteurs, sémantique d'invocation/finalisation
- Ordre du moteur : nouveau mode `--ordering scion`. Les émissions enfant→parent sont mises en file d'attente normalement; `done.invoke` est poussé en tête avec générique avant spécifique à l'ID pour mieux correspondre à [SCION](https://www.npmjs.com/package/scion).

## Recettes de Reproduction
Tests unitaires
- Tous les tests Python : `PYTHONPATH=py pytest -q py/tests`
- Test unique : `PYTHONPATH=py pytest -q py/tests/test_engine.py::test_invoke_generic_done_event`

Résultat du moteur
- `PYTHONPATH=py python -m scjson.cli engine-verify -I tutorial/Tests/python/W3C/Mandatory/Auto/test253.scxml --xml --advance-time 3`
- 401 : `PYTHONPATH=py python -m scjson.cli engine-verify -I tutorial/Tests/python/W3C/Mandatory/Auto/test401.scxml --xml`

Comparaison de traces
- Principal : `python py/exec_compare.py <chart.scxml> --events <events.jsonl>`
- Optionnel : `--keep-step0-states` pour conserver `enteredStates`/`exitedStates` de l'étape 0
- Le repli de référence est résolu automatiquement vers `node tools/scion-runner/scion-trace.cjs`; remplacer via `SCJSON_REF_ENGINE_CMD`

Harnais Uber (conversion inter-langues)
- Chemin : `py/uber_test.py`
- "Smoke" du moteur Python (paramétré) : `PYTHONPATH=py pytest -q -k "uber_test and executes_chart"`
- "Smoke" CLI avec progression : `python py/uber_test.py --python-smoke [--chart <path>]`

## Différences Connues et Notes
- La visibilité de l'initialisation varie selon les moteurs; la normalisation à l'étape 0 atténue les différences
- Les ID d'invocation diffèrent; non pertinent du point de vue comportemental
- Les processeurs externes (HTTP) ne sont toujours pas pris en charge; les tests qui en dépendent sont laissés dans `ENGINE_KNOWN_UNSUPPORTED`

## Prochaines Étapes
- Balayage plus large des tutoriels et réductions incrémentielles de la liste d'exclusion
- Valider plus de graphiques avec exec_compare et ajuster la normalisation uniquement si nécessaire
- Envisager de marquer le "smoke" paramétré comme `@pytest.mark.slow` et d'utiliser des filtres `-k` par défaut

## Greps Pratiques
- Sauter aux points clés :
  - `rg -n "_emit_error|_select_transition|finalize|#_parent|invokeid|error\.execution|error\.communication" py`
  - `rg -n "engine-verify|engine-trace" py/scjson/cli.py`
  - `rg -n "InvokeRegistry|SCXMLChildHandler|send\(\)" py/scjson/invoke.py`
  - `rg -n "advance_time|control token|advance-time" py`
