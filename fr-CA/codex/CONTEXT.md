```markdown
<p align="center"><img src="../scjson.png" alt="scjson logo" width="200"/></p>

Agent Name: python-engine-todo

Fait partie du projet scjson.
Développé par Softoboros Technology Inc.
Sous licence BSD 1-Clause.

# Moteur d'exécution Python — Plan de vérification

Cette liste de vérification retrace le travail visant à transformer le runtime Python actuel (modules DocumentContext + Activation/Événement) en un moteur d'exécution SCXML complet, validé par un moteur de référence canonique.

## Portée et objectifs
- [ ] Implémenter l'algorithme d'exécution SCXML (macro-étape/micro-étape), le traitement des événements, la sélection des transitions, la résolution des conflits et la gestion de la configuration.
- [ ] Supporter les états composés, parallèles, finaux et d'historique (superficiels/profonds) avec une sémantique d'achèvement correcte.
- [ ] Implémenter le contenu exécutable : assign, log, raise, if/elseif/else, foreach, script, send/cancel, invoke/finalize, param/content.
- [x] Fournir une interface CLI pour exécuter un graphique par rapport à un script d'événements et émettre une trace JSON déterministe pour comparaison. (`scjson engine-trace`)
- [ ] Valider le comportement sur un corpus standard en comparant les traces avec un moteur canonique.
  - [x] Ajouter les options exec_compare (bascule feuille seulement, omettre des champs, contrôles étape-0, avance de temps python) et un outil de balayage (`py/exec_sweep.py`).

## Sémantique de référence
- [x] Décider du moteur de référence canonique.
  - [x] Utiliser scion-core (Node.js) comme référence canonique pour le comportement.
  - [x] Documenter la justification et les directives pour la compatibilité scion dans la documentation du dépôt. (`py/scjson/ENGINE.md`)
- [ ] Fournir une comparaison avec Apache Commons SCXML 0.x comme référence historique si nécessaire (facultatif, pour la parité historique).

Notes de décision (ordre invoke/finalize)
- L'ordre de finalisation entre plusieurs invocations se terminant à la même étape est traité comme défini par l'implémentation dans notre moteur par défaut. Nous nous référons au comportement de [SCION](https://www.npmjs.com/package/scion) lorsqu'il est observable et stable, mais les tests sont tolérants (présence des deux événements émis par finalize) pour éviter de sur-contraindre l'ordre dans les régions parallèles. Une fois que le comportement de [SCION](https://www.npmjs.com/package/scion) est confirmé stable pour ces graphiques, nous pourrons verrouiller un ordre déterministe (par exemple, ordre de document/création) et resserrer les tests en conséquence.

## Feuille de route (Itérations)

1) Algorithme de base et trace
- [x] Faire de `scjson.context` la source unique du runtime (retirer/redéfinir `engine.py`).
- [x] Implémenter la boucle de macro-étapes (traiter les transitions sans événement jusqu'à la quiescence).
- [x] Sélection déterministe des transitions (ordre de document, vérifications d'ancêtres, résolution de conflits).
- [x] Définir un schéma de trace JSON standardisé (event, firedTransitions, enteredStates, exitedStates, configuration, actionLog, datamodelDelta).
- [x] Ajouter CLI : `scjson engine-trace -I chemin.[scxml|scjson] [--xml] -e events.jsonl`.

2) Composé, Parallèle, Final, Historique
- [x] Calculer les ensembles de sortie/entrée via LCA ; gestion correcte des ancêtres/descendants.
- [x] Achèvement parallèle : le parent est final lorsque toutes les régions sont terminées ; propager la finalisation.
- [x] Historique : superficiel avec repli par défaut de transition.
- [x] Historique : profond (restaurer les descendants profonds).
- [x] Parallèle : l'entrée initiale entre dans toutes les régions enfants.

3) Contenu exécutable Phase 1
- [x] Implémenter assign, log, raise dans les corps onentry/onexit/transition.
- [x] Implémenter if/elseif/else.
- [x] Implémenter foreach.
- [x] Remplacer `eval` par un évaluateur d'expressions/sandbox sécurisé ; documenter le modèle de confiance et ajouter `--unsafe-eval` pour les exécutions fiables.

4) Événements, temporisateurs et E/S externes
- [x] `EventQueue` interne de base pour les événements externes/internes.
- [x] `<send>` (délai, cible), `<cancel>` par ID ; puits externes.
- [x] Émettre les événements d'erreur (`error.execution`, `error.communication`, …) dans la trace.
- [x] Temporisateurs avec horloge fictive pour les tests déterministes. (La planification de `<send>` retardés utilise `DocumentContext.advance_time` pour un contrôle déterministe.)

5) Invoke / Finalize
 - [x] Ajouter l'échafaudage : InvokeRegistry + gestionnaire simulé ; démarrer/annuler à l'entrée/sortie d'état ; `<finalize>` s'exécute à l'achèvement/annulation ; émet `done.invoke` et `done.invoke.<id>`.
 - [x] Implémenter le cycle de vie de base de `<invoke>` avec `autoforward` et bullage enfant.
 - [x] Supporter l'enfant `<send target="#_parent">` et le parent `<send target="#_child">`.
 - [x] Gérer `<invoke><content>` SCXML en ligne et les URI de fichier, normalisation des URI de type.
 - [x] Compléter le mappage `<param>`/`<content>` et l'exposition de `_event` pour la finalisation (tests ajoutés).
 - [x] Étendre le registre : `mock:immediate`, `mock:record`, `mock:deferred`, `scxml`/`scjson` enfant ; tests d'ordonnancement et de concurrence.

6) Robustesse et performance
- [x] Modes d'exécution souple ou strict ; comportement des éléments/attributs inconnus.
- [x] Dimensionnement des instantanés/filtres de journaux ; ordre reproductible pour les ensembles. (engine-trace : --leaf-only, --omit-actions, --omit-delta, --omit-transitions ; ordre déterministe pour datamodelDelta)
 - [x] Mettre à jour `ENGINE.md` pour qu'il corresponde à l'implémentation et au schéma de trace.

## Instantané de l'état — 2025-09-30
- Le moteur exécute `if`/`elseif`/`else`, `foreach`, `<send>` (immédiat + différé), `<cancel>`, et les corps de transition dans l'ordre d'auteur.
- Achèvement parallèle : émet des événements `done.state.<regionId>` par région et `done.state.<parallelId>` lorsque toutes les régions sont finales. Les états composés émettent `done.state.<parentId>` avec une charge utile `<donedata>`.
- Historique : restauration superficielle et profonde prise en charge. Les actions de transition d'historique par défaut s'exécutent lorsqu'aucun instantané n'existe.
- Les tâches `<send>` différées sont planifiées par rapport à `DocumentContext` et avancées de manière déterministe avec `advance_time` ; les cibles externes mettent en file d'attente `error.communication` et sont ignorées.
- Événements d'erreur : `cond` non booléen/échoué, erreurs de tableau `<foreach>`, et échecs d'évaluation `<assign>` mettent en file d'attente `error.execution`.
  - Les événements d'erreur générés par le moteur sont prioritaires en tête de file d'attente afin qu'ils soient traités avant les événements normaux mis en file d'attente ultérieurement.
- Le balayage du tutoriel (`py/uber_test.py::test_python_engine_executes_python_charts`) respecte `ENGINE_KNOWN_UNSUPPORTED` et est réduit à mesure que les fonctionnalités sont implémentées.
- Les blocs de texte `<send><content>` sont normalisés lors de l'ingestion JSON ; les attributs de localisation reçoivent des ID auto-générés avant la validation Pydantic.
- Les tests d'intégration couvrent les charges utiles textuelles, d'expression et de balisage imbriqué émises par `<send>`.
- La documentation dans `py/scjson/ENGINE.md` décrit les événements terminés, la sémantique de l'historique, l'ordonnancement du corps de transition et les événements d'erreur.
- Couverture d'invocation (W3C) : avec avance de temporisateur (`--advance-time 3`), les tests 253, 338, 422, 554 réussissent via `engine-verify`.

## Stratégie de test

Exécuteur de moteur de référence
- [ ] Implémenter un wrapper d'exécuteur Java (préféré) :
  - [ ] Charger SCXML avec Commons SCXML2, consommer les événements JSONL sur stdin, émettre une trace standardisée sur stdout.
  - [ ] Packager en tant que cible d'exécution Maven ou fat-jar sous `java/runner`.
- [x] Implémenter un wrapper d'exécuteur Node (repli, si l'exécuteur Java n'est pas réalisable) : script `scion-core` léger émettant le même format de trace (voir `tools/scion-runner/scion-trace.cjs`).

Artefacts et jeux de données
- [ ] Utiliser le sous-module de tutoriel + les tests W3C permis comme corpus standard.
- [x] Ajouter `tests/exec/` avec des graphiques sélectionnés et des scripts d'événements JSONL.
- [x] `py/uber_test.py` balaye les graphiques Python du tutoriel avec une gestion `ENGINE_KNOWN_UNSUPPORTED` sensible aux sauts et une sortie agrégée des échecs.

Schéma de trace (JSON par ligne)
- [x] `step` : entier.
- [x] `event` : `{ name, data } | null`.
- [x] `firedTransitions` : `[{ source, targets:[...], event, cond }]`.
- [x] `enteredStates` : `[stateId]`.
- [x] `exitedStates` : `[stateId]`.
- [x] `configuration` : `[stateId]` (trié).
- [x] `actionLog` : `[string]` (facultatif ; ordre stable).
- [x] `datamodelDelta` : `{ key: newValue }` (facultatif ; seules les clés modifiées).

Logique du harnais
- [x] L'exécuteur Python produit `py.trace.jsonl`.
- [x] L'exécuteur de référence produit `ref.trace.jsonl`.
- [x] Normaliseur pour l'ordonnancement et la normalisation de type simple.
- [x] Diff pas à pas et résumé (première étape différente, nombre de non-concordances).
- [x] Rapporter les totaux similaires à `uber_test` (fichiers et non-concordances d'éléments).

Ajouts CLI (Python)
- [x] Implémenter `scjson engine-trace`.
- [x] Entrées : `--xml`, `-I/--input`, `-e/--events`, `-o/--out`.
 - [x] Options :
  - [x] `--lax/--strict`
  - [x] `--unsafe-eval` (désactivé par défaut)
  - [x] `--max-steps`

Outils de comparaison
- [x] Ajouter `py/exec_compare.py` pour piloter les deux exécuteurs et les traces de différence avec des codes de sortie compatibles CI.
- [x] Supporter les comparaisons secondaires facultatives via les remplacements CLI/env.

## Jalons et livrables
- [ ] M1 : Trace de base + macro-étape + CLI ; tests unitaires de trace ; 10 graphiques simples passent par rapport à l'exécuteur choisi.
- [ ] M2 : Parallèle + finalisation + historique superficiel ; corpus étendu ; documentation d'utilisation de l'exécuteur.
- [ ] M3 : Évaluateur d'expressions sécurisé ; conformité du contenu d'exécution ; couverture accrue.
- [ ] M4 : send/cancel/timers avec horloge simulée ; événements d'erreur ; schéma de trace stabilisé.
- [ ] M5 : invoke/finalize avec des simulations ; tâche CI pour la différence de corpus complet.

## Risques et atténuations
- [ ] Décider du moteur de référence si les problèmes Maven bloquent Java ; passer à une alternative gratuite avec une autorité comparable (par exemple, scion-core).
- [x] Contraindre les fonctionnalités d'expression à un sous-ensemble inter-moteur ou injecter via les données d'événement ; fournir un mode Python-seulement pour les expressions avancées. (sandbox sécurisé par défaut ; préréglages via --expr-preset avec --expr-allow/--expr-deny facultatifs ; évaluation Python avec --unsafe-eval)
- [ ] Appliquer un ordre déterministe lorsque SCXML permet le choix de l'implémentation.

## Critères d'acceptation
- [ ] Les traces Python correspondent aux traces de référence pour le corpus sélectionné (configuration, transitions déclenchées, actions d'entrée/sortie).
- [ ] Le travail de CI exécute le harnais et ne signale aucune non-concordance.
- [ ] La documentation (`ENGINE.md`, ce TODO, l'aide CLI) est mise à jour.

## Prochaines étapes immédiates
 - [x] Mettre à jour `py/scjson/ENGINE.md` avec les limitations actuelles (liste d'ignorés, `<script>` noop, cibles d'envoi externes) et les directives d'évaluation sécurisée.
- [x] Ajouter des tests unitaires ciblés couvrant la planification/annulation de `<send>` différés via `DocumentContext.advance_time`.
- [x] Ajouter une couverture d'intégration pour les charges utiles `<send><content>` normalisées afin d'assurer la parité avec scion-core. (`py/tests/test_engine.py::test_send_content_*`)
- [x] Ajouter des tests ciblés pour l'historique profond à travers les parallèles et la précédence des données (le contenu domine les paramètres).
- [x] Ajouter des tests d'ordonnancement pour `error.execution` et `error.communication` par rapport aux événements normaux ; prioriser les événements d'erreur dans la file d'attente.
- [x] Finaliser l'évaluation en parallèle (234) : Ajout d'une unité garantissant que seul le `<finalize>` de l'invocation en cours d'achèvement s'exécute et que les frères et sœurs annulés ne le font pas. (`py/tests/test_engine.py::test_finalize_only_runs_in_invoking_state_in_parallel`)
- [x] Métadonnées d'E/S d'événements SCXML : `_event.origintype` et `_event.invokeid` remplies pour les envois enfant↔parent ; cible explicite `#_<invokeId>` parent→enfant prise en charge.
- [x] Sémantique de démarrage d'invocation : exécuter `<invoke>` à la fin de la macro-étape pour les états entrés et non sortis ; implémenter la correspondance multi-événements pour les transitions (`event="a b"`).
- [x] Balayage W3C (253/338/422/554) : les résultats `engine-verify` sont passants lors de l'utilisation de `--advance-time` ; la normalisation feuille-seulement `exec_compare` correspond au 554 ; d'autres diffèrent à l'étape 0 en raison de la visibilité de la transition initiale. La normalisation de l'étape 0 supprime maintenant `datamodelDelta` et `firedTransitions`, avec suppression facultative de `enteredStates`/`exitedStates` régie par `--keep-step0-states`.
- [x] Émettre un alias `error` générique à côté de `error.execution` pour améliorer la compatibilité avec les graphiques écoutant `error.*`.
- [x] Ajouter une gestion des assignations invalides conforme aux spécifications : l'assignation à un emplacement non existant met maintenant en file d'attente `error.execution` et ne crée pas de nouvelle variable ; cela active le test W3C `test401.scxml`. Supprimé de `ENGINE_KNOWN_UNSUPPORTED`.
- [ ] Revoir `ENGINE_KNOWN_UNSUPPORTED` dans `py/uber_test.py` et planifier les suppressions à mesure que les fonctionnalités sont implémentées.

Nouveaux éléments de travail (plan mis à jour)
- [ ] Invoke/finalize
  - [ ] Examiner l'ordonnancement de finalisation de [SCION](https://www.npmjs.com/package/scion) pour plusieurs achèvements simultanés ; si stable, adopter la même politique déterministe (par exemple, ordre de document) et resserrer les tests d'ordonnancement ; sinon, maintenir les vérifications de présence tolérantes.
  - [ ] Ajouter un bouton CI pour exécuter des comparaisons basées sur [SCION](https://www.npmjs.com/package/scion) sur un sous-ensemble de graphiques invoke/finalize lorsque Node est disponible.
- [ ] Génération de vecteurs (Phase 3)
  - [ ] Minimisation préservant les deltas, axée sur les firedTransitions et enteredStates uniques.
  - [ ] Heuristiques pour les disjonctions et les structures imbriquées ; étendre la construction de charge utile négative.
  - [x] Injection facultative de advance_time dans les séquences lorsque des envois différés sont détectés après l'initialisation.
  - [ ] Étendre le corpus de balayage avec plus de combinaisons parallèle + historique + invocation et des graphiques de variance étape-0.
  - [ ] Documentation
  - [x] docs/ENGINE-PY.md : ajouter une section "Sémantique Invoke & Finalize" décrivant done.invoke spécifique à l'ID vs générique, le comportement finalize-before-done dans la même micro-étape, et les notes d'ordonnancement en parallèle.

## Génération de vecteurs et couverture (nouvelle initiative)

Objectif : Générer automatiquement des vecteurs d'événements pour chaque graphique afin de maximiser la couverture comportementale et de comparer les traces Python avec scion pour ces vecteurs. Cela remplace les fixations ad hoc par un processus répétable et échelonnable.

Composants planifiés
- Analyseur et alphabet
  - Extraire les jetons d'événement de transition (listes divisées ; ignorer les modèles génériques/préfixes), les indices done/state et invoke.
- Simulateur et couverture
  - Suivre les états entrés, les transitions déclenchées et les événements done/error à partir des traces du moteur.
- Recherche vectorielle (bornée)
  - BFS guidé par la couverture sur l'alphabet d'événements (profondeur ≤ 2-3), élaguer en l'absence de delta.
  - Inclure "complete" lorsque mock:deferred invoke est présent ; insérer advance_time si nécessaire.
- Heuristiques de charge utile (Phase 2)
  - Basculer les booléens/numériques simples des identifiants cond/expr pour inverser les branches.
  - Détecter automatiquement les envois différés lors de l'initialisation et recommander un advance_time.
- Émission et comparaison
  - Émettre les vecteurs sous forme de `.events.jsonl` + `.coverage.json`, intégrer avec `exec_compare --generate-vectors` et `exec_sweep --generate-vectors`.
- Minimisation et rapport
  - Tronquer les vecteurs ; agréger la couverture sur les graphiques dans un résumé de balayage.

Livrables
- `py/vector_gen.py`, `py/vector_lib/*` : générateur + aides
- `py/exec_compare.py` : drapeaux d'intégration vectorielle et affichage de la couverture
- `py/exec_sweep.py` : génération de vecteurs, agrégation de couverture, résumé JSON dans le répertoire de travail

Phases et listes de vérification
- Phase 1 (implémentée) : générateur de base, BFS à profondeur limitée, sidecar de couverture, intégration de comparaison.
- Phase 2 (implémentée) : heuristiques de charge utile et inversion de branche, détection d'auto-avance, limites.
  - [x] L'analyseur extrait les chemins `_event.data` et les comparateurs de `cond`.
  - [x] Appartenance (y compris les conteneurs inversés et de modèle de données) ; plages chaînées/divisées.
  - [x] La recherche accepte les stimuli porteurs de données et simule les charges utiles.
  - [x] Fusion de charge utile à un seul point pour inverser les branches ; limitée par `--variants-per-event`.
  - [x] Le générateur émet des événements avec des charges utiles `data` et écrit des sidecars :
        ``.coverage.json`` et ``.vector.json`` (avec indice ``advanceTime``).
  - [x] exec_compare/exec_sweep adoptent ``advanceTime`` de ``.vector.json``
        lorsque ``--advance-time`` n'est pas explicitement fourni.
  - [x] Ajouter les boutons `--variants-per-event` sur vector_gen/compare/sweep.
- Phase 3 : raffinements et minimisation parallèle/invocation.
```

## Commandes de reproduction
Tests unitaires (Python)
- `PYTHONPATH=py pytest -q py/tests`
- Test unique : `PYTHONPATH=py pytest -q py/tests/test_engine.py::test_name`
 - Fumée paramétrée sur les graphiques du tutoriel (un test par graphique) :
   - Tous : `PYTHONPATH=py pytest -q -k "uber_test and executes_chart"`
   - Filtrer par nom : `PYTHONPATH=py pytest -q -k "executes_chart and history_shallow.scxml"`

Résultat du moteur (graphiques W3C)
- `PYTHONPATH=py python -m scjson.cli engine-verify -I tutorial/Tests/python/W3C/Mandatory/Auto/test253.scxml --xml --advance-time 3`
- Idem pour : 338, 422, 554 → résultat actuel : passe
- 401 (précédence d'erreur générique) passe maintenant grâce à la sémantique d'assignation invalide + alias :
  - `PYTHONPATH=py python -m scjson.cli engine-verify -I tutorial/Tests/python/W3C/Mandatory/Auto/test401.scxml --xml`

Comparaison de trace avec la référence
- Principal : `python py/exec_compare.py <graphique.scxml> --events <événements.jsonl>`
- Valeurs par défaut : exécuteur de référence `node tools/scion-runner/scion-trace.cjs` si disponible
- Facultatif : `--keep-step0-states` pour préserver les `enteredStates`/`exitedStates` de l'étape 0
- Remplacement d'environnement : `SCJSON_REF_ENGINE_CMD` pour fournir une commande de référence

Configuration de l'exécuteur Node (si nécessaire)
- Le dépôt inclut `tools/scion-runner/scion-trace.cjs` et `node_modules`.
- Utiliser directement : `node tools/scion-runner/scion-trace.cjs --help`

## État actuel et vérifications
Suite de tests unitaires du moteur
- Statut : vert (les tests Python passent)
- Les vérifications ciblées incluent : historique profond, ordonnancement parallèle de finalisation, normalisation du contenu d'envoi, priorité des événements d'erreur, portée de finalisation d'invocation, ciblage `#_<invokeId>` explicite, correspondance de motifs d'événements, gestion des jetons de contrôle CLI, et injection d'avance de temps vectorielle.

Points saillants W3C/Tutoriel
- W3C obligatoire : 253/338/422/554 passent avec `--advance-time 3`
- W3C obligatoire : 401 passe maintenant (assignation invalide → `error.execution` + l'alias `error` assure la précédence d'erreur générique)
- Graphiques de tutoriel de modèle de données Python découverts : 208
- Échantillon ad hoc de 50 graphiques de modèle de données Python : aucune erreur de construction de traces (`DocumentContext.from_xml_file(...).trace_step()`)

Maintenance de la liste d'ignorés
- `py/uber_test.py::ENGINE_KNOWN_UNSUPPORTED` n'inclut plus W3C test401
- Les entrées restantes sont des tests facultatifs sans rapport avec la portée actuelle (processeurs HTTP, etc.)

## Notes de comportement
Normalisation de la trace étape-0
- Les moteurs diffèrent sur la visibilité de la transition initiale ; la normalisation supprime par défaut `datamodelDelta` et `firedTransitions` de l'étape 0
- Supprimer éventuellement aussi les listes d'entrée/sortie de l'étape 0 pour réduire le bruit de différence

Correspondance d'événements
- Accepte les noms d'événements séparés par des espaces, le caractère générique `*` et les motifs de préfixe comme `error.*`

Ordonnancement des événements d'erreur
- `error.execution` est push-front ; émet également un `error` générique (pas push-front par défaut sauf si explicitement nécessaire pour préserver la sémantique d'ordonnancement onentry)
- `error.communication` n'émet pas d'alias pour éviter l'intercalation avec des événements explicites

Invoquer
- Finalize s'exécute dans l'état d'invocation avec un dictionnaire `_event` (`name`, `data`, `invokeid`, et tout origin/origintype)
- L'ordonnancement des exécutions se fait par défaut spécifique à l'ID puis générique ; la préférence est ajustée lorsque les enfants émettent des événements lors de l'initialisation pour préserver l'ordonnancement observé
- Démarrage en fin de macro-étape : uniquement pour les états toujours actifs à la fin de l'étape

## Ce qui a changé cette session
- engine-trace : accepte les jetons de contrôle `{"advance_time": N}` dans les événements JSONL ; fait avancer l'horloge simulée sans émettre d'étape.
- vector_gen : injecte des jetons de contrôle `advance_time` entre les stimuli lorsque des temporisateurs sont en attente après une étape.
- Tests : ajout d'un test de jeton de contrôle CLI ; ajout de graphiques sweep_corpus organisés et de tests exec_compare avancés.
- Wrapper : ajout de `py/py/exec_compare.py` pour les tests invoquant ce chemin.
- uber_test : tests paramétrés par graphique pour un retour plus rapide ; `python py/uber_test.py --python-smoke` affiche la progression et le statut par graphique.
- Docs : `docs/ENGINE-PY.md` mis à jour avec les jetons de contrôle, l'injection d'avance de temps vectorielle et la sémantique invoke/finalize.
- Ordonnancement du moteur : ajout d'une politique d'`ordering` explicite avec le mode `scion`. En mode `scion`, les émissions enfant→parent sont mises en file d'attente normalement tandis que `done.invoke` est poussé en tête (générique avant spécifique à l'ID) pour s'aligner sur le comportement de micro-étape de [SCION](https://www.npmjs.com/package/scion).

## Prochaines étapes (suggérées)
- Facultatif : marquer les tests uber paramétrés `@pytest.mark.slow` pour les exclure des exécutions par défaut ; préférer les filtres `-k` ciblés pour l'itération.
- Élargir le corpus organisé ; faire évoluer les heuristiques vectorielles pour une couverture plus approfondie.

## Liste de vérification de reprise rapide
- Exécuter la suite d'unités : `PYTHONPATH=py pytest -q py/tests`
- Vérifier l'ensemble rapide W3C : 253/338/422/554/401 avec `engine-verify`
- Pour les différences par rapport à la référence, utiliser `py/exec_compare.py` avec ou sans `--keep-step0-states`
- Lors de l'édition du comportement invoke/child, retester :
  - `py/tests/test_engine.py::test_invoke_*`
  - tests de bullage enfant et d'ordonnancement de finalisation
 - Fumée Python avec progression :
   - `python py/uber_test.py --python-smoke`
   - `python py/uber_test.py --python-smoke --chart tutorial/Tests/python/W3C/Mandatory/Auto/test253.scxml`

Grep rapide
- `rg -n "_emit_error|_select_transition|finalize|#_parent|invokeid|error\.execution|error\.communication" py` pour sauter au code pertinent
 - `rg -n "advance_time|control token|advance-time" py`
```
