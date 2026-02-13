```markdown
<p align="center"><img src="../scjson.png" alt="scjson logo" width="200"/></p>

Agent Name: ruby-engine-todo

Fait partie du projet scjson.
Développé par Softoboros Technology Inc.
Sous licence BSD 1-Clause Licence.

# Moteur d'exécution Ruby — Plan de la liste de contrôle

Cette liste de contrôle suit le travail visant à livrer un moteur d'exécution Ruby avec un comportement entièrement compatible avec [SCION](https://www.npmjs.com/package/scion) et une parité linguistique croisée avec le moteur Python. Le plan couvre également l'empaquetage, la documentation et l'intégration dans le harnais de validation existant.

## Portée et objectifs
- [ ] Implémenter l'algorithme d'exécution SCXML (macro/micro-étape), le traitement des événements, la sélection des transitions, la résolution des conflits, la gestion de la configuration.
- [ ] Atteindre une sémantique entièrement compatible avec SCION pour Ruby, en faisant correspondre les traces sur un corpus partagé (normalisation autorisée le cas échéant).
- [ ] Refléter d'abord les capacités du moteur Python (document unique), puis étendre au comportement complet équivalent à SCION pour plusieurs documents (invocation/finalisation, machines enfants, événements terminés).
- [ ] Maintenir la pipeline de validation identique à Python : utiliser le harnais Python pour évaluer l'exécution du moteur Ruby par rapport à SCION et/ou Python.
- [ ] Convertir les documents de test actuellement adaptés à JS et Python en extensions de vecteurs de test Ruby (uniquement en interne ; ne pas modifier le contenu du tutoriel).
- [ ] Fournir un guide d'utilisation dédié au moteur Ruby (comme celui de Python), avec des détails plus approfondis et des exemples exécutables.
- [ ] Mettre en évidence le moteur Ruby en haut du README et mentionner l'exécution SCXML/SCML dans la description, les métadonnées du paquet et les termes de recherche.
- [ ] Améliorer le support de la documentation RubyGems et ajouter les détails du paquet RubyGems à la section inférieure du README.
- [ ] Augmenter la version du projet à 0.3.5 dans le cadre de la publication incluant le moteur Ruby.

## Sémantique de référence
- [ ] Utiliser [SCION](https://www.npmjs.com/package/scion) (Node) comme référence comportementale.
- [ ] Comparer les traces du moteur Ruby avec celles de SCION et Python via les outils du harnais Python.
- [ ] Documenter tout ordre défini par l'implémentation ou les deltas connus et fournir des drapeaux de normalisation cohérents avec Python.

## Feuille de route (Itérations)

1) Amorçage et parité avec Python (document unique)
- [x] Définir le cœur du runtime Ruby (contexte du document, configuration, file d'attente d'événements, règles de sélection/conflit — de base, transition unique).
- [x] Implémenter les transitions sans événement vers la quiescence (macro-étape de base ; bornée).
- [x] Implémenter l'ordonnancement des sorties/entrées basé sur LCA pour les micro-étapes à transition unique (de base ; configuration uniquement par feuilles).
- [x] Évaluation des conditions de transition (de base : littéraux, variables, ==/!=, comparaisons numériques).
- [ ] Implémenter la boucle complète de macro-étape et la résolution complète des conflits pour correspondre à Python.
- [x] Contenu exécutable Phase 1 (sous-ensemble) : log, assign (littéraux et incréments +N), raise, if/elseif/else, foreach.
- [x] E/S d'événements : file d'attente interne, événements d'erreur ; temporisateurs via horloge simulée (jeton de contrôle advance_time accepté dans les flux d'événements pour correspondre aux traces déterministes de Python).
- [x] CLI : `scjson engine-trace` en Ruby, émettant des traces JSONL déterministes (même schéma que Python).
- [x] Intégrer avec `py/exec_compare.py` comme moteur "secondaire" testé (utiliser `--secondary "ruby/bin/scjson engine-trace"`).

2) Multi-documents et invocation/finalisation
- [x] Implémenter le cycle de vie `<invoke>`, `<finalize>`, les événements `done.invoke`/`done.invoke.<id>` (détection de base immédiate et de fin d'enfant) ; ordonnancement mis en tampon avec `--ordering scion`.
- [x] Support des machines enfants (SCXML/SCJSON en ligne et fichiers : URIs) ; cibles `#_parent`, `#_child`/`#_invokedChild` et `#_<id>` ; `autoforward`.
- [x] Support des machines enfants (en ligne et fichiers `src`) ; cibles `#_parent`, `#_child`/`#_invokedChild` et `#_<id>` ; `autoforward`.
- [x] Achèvement parallèle (de base), cibles d'historique (superficiel/profond) et sémantique des états finaux ; événements `done.state.<id>` en file d'attente.
- [ ] Gestion des erreurs et ordonnancement cohérents avec SCION ; adopter les options de normalisation de Python le cas échéant.
  - [x] `<cancel>` implémenté avec la gestion des temporisateurs basée sur l'ID ; émet `error.execution` si l'ID est manquant/introuvable.
  - [x] Évaluateur : `in(stateId)`, parcours `_event.data` sécurisé contre les valeurs nulles et égalité de types mixtes (chaîne numérique vs nombre).
  - [x] Invocation : propager le `<donedata>` enfant à la charge utile `done.invoke` ; ordonnancement mis en tampon respecté (`--ordering scion`).
  - [x] Ajouter l'option `--defer-done` (activée par défaut) pour reporter le traitement de `done.invoke*` à l'étape suivante afin de correspondre aux limites d'étape de SCION.
  - [ ] Renforcer davantage la résolution des conflits de transition pour les cas limites imbriqués/parallèles ; ajouter des tests ciblés.

3) Intégration du harnais de validation
- [ ] Connecter le CLI Ruby à `py/exec_compare.py` et `py/exec_sweep.py` (chaîne de commande + hypothèses du répertoire de travail documentées).
- [x] Normaliser les traces avec les contrôles feuille-seulement/omit-delta/étape-0 reflétant les drapeaux Python (`--strip-step0-noise`, `--strip-step0-states`, `--keep-cond`).
- [ ] Cible CI pour exécuter un sous-ensemble de graphiques sur chaque PR contre SCION et Python.

4) Documentation et exemples
- [x] Créer `docs/ENGINE-RB.md` (guide de l'utilisateur) reflétant la structure de `docs/ENGINE-PY.md`.
- [x] Ajouter `ruby/ENGINE-RB-DETAILS.md` (architecture et référence approfondie) analogue à `py/ENGINE-PY-DETAILS.md`.
- [x] Porter les flux d'événements d'exemple JS/Python vers des exemples centrés sur Ruby (sans modifier `tutorial/`) : membership, invoke_inline, invoke_timer, parallel_invoke.
- [x] Ajouter des conseils de dépannage et de normalisation (étape-0, temporisateurs, limitations d'expression) dans `docs/ENGINE-RB.md`.

5) Empaquetage et publication
- [x] Améliorer le support de documentation RubyGems : sections README, hooks YARD/RDoc, liens vers la page d'accueil et la source, résumé/description étendue.
- [ ] Mettre à jour les mots-clés des métadonnées du gem (termes de recherche) : "scxml", "statecharts", "state-machine", "scjson", "scml", "execution".
- [x] Mises à jour du README : mettre en évidence le moteur Ruby en haut ; ajouter les détails du paquet RubyGems en bas.
- [x] Augmenter la version à 0.3.5 dans tout le dépôt (paquets Python, Ruby et JS mis à jour).

## Vecteurs de test et corpus
- [ ] Convertir les documents de test JS/Python en extensions de vecteurs Ruby hébergées dans le dépôt (par exemple, des variantes `tests/exec/*.events.jsonl` si Ruby nécessite des jetons de temporisation). Ne pas modifier le contenu de `tutorial/`.
- [ ] S'assurer que le harnais Python peut sélectionner Ruby comme cible via `-l ruby` et agréger la couverture dans `uber_out/`.
- [ ] Ajouter un petit corpus spécifique à Ruby pour exercer la sémantique multi-document (invocation/finalisation).

## Critères d'acceptation
- [ ] Les traces du moteur Ruby correspondent à SCION sur le corpus canonique (après normalisation) et correspondent à Python sur des sous-ensembles partagés.
- [ ] La tâche CI exécute `exec_compare` pour Ruby vs SCION et ne rapporte aucune non-concordance sur la suite d'acceptation.
- [ ] `docs/ENGINE-RB.md` et `ruby/ENGINE-RB-DETAILS.md` sont publiés avec des exemples exécutables.
- [ ] Le README met en évidence le moteur Ruby ; les liens et métadonnées RubyGems sont mis à jour.
- [ ] La version du dépôt est passée à 0.3.5 et les artefacts publiés sont tagués.

## Prochaines étapes immédiates
- [x] Ébaucher un document de parité de schéma de trace pour Ruby (réutiliser le schéma et les drapeaux Python).
- [x] Ajouter une commande stub Ruby CLI `engine-trace` qui imprime une ligne de trace statique pour valider le câblage du harnais, puis itérer.
- [x] Ajouter l'intégration du harnais à `py/exec_compare.py` pour invoquer le CLI Ruby et analyser la sortie de trace (via `--secondary`).
- [ ] Préparer les exemples Ruby initiaux et les flux `.events.jsonl` correspondants (avec `advance_time` si des temporisateurs sont utilisés).
 - [x] Implémenter les temporisateurs : `<send delay>` avec jeton de contrôle `advance_time` pour vider les événements planifiés de manière déterministe.

## Risques et atténuations
- [ ] Différences d'évaluation des expressions entre les langages : contraindre à un sous-ensemble inter-moteur ; fournir un mode optionnel Ruby-seulement signalé dans les documents.
- [ ] Nuances de temporisation et d'ordonnancement des événements : conserver les commutateurs de normalisation Python ; tester avec les contrôles `advance_time`.
- [ ] Différences d'ordonnancement de finalisation multi-documents : documenter la politique et, si nécessaire, adopter strictement l'ordonnancement SCION en mode "scion".

## Instantané du statut — 2025-10-03
- `Les types de CLI et de schéma du convertisseur existent dans ruby/lib/scjson.` - Pas de changement.
- `La commande stub CLI de trace du moteur a été ajoutée (scjson engine-trace) ; le harnais peut appeler Ruby via --secondary.` - Pas de changement.
- `Les squelettes de documentation ont été ajoutés (docs/ENGINE-RB.md, ruby/ENGINE-RB-DETAILS.md).` - Pas de changement.
 - `Les temporisateurs sont pris en charge (envoi retardé + advance_time), les événements internes, les tests d'appartenance et les littéraux JSON.` - Pas de changement.
 - `Invocation : contextes enfants (en ligne + src), routage parent↔enfant, autoforward, mappage des paramètres et ordonnancement de done.invoke mis en tampon avec --ordering.` - Pas de changement.
 - `L'entrée initiale parallèle a été corrigée pour plusieurs régions.` - Pas de changement.

---

Retour à
- Guide d'utilisation du moteur Python : `docs/ENGINE-PY.md`
- Matrice de compatibilité : `docs/COMPATIBILITY.md`
- Aperçu du projet : `README.md`
```
