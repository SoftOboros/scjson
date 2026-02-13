<p align="center"><img src="../scjson.png" alt="scjson logo" width="200"/></p>

Nom de l'agent: ruby-engine-details

Fait partie du projet scjson.
Développé par Softoboros Technology Inc.
Sous licence BSD 1-Clause License.

# Moteur Ruby — Architecture et détails

Ce document décrit l'architecture, les objectifs de conception et les notes d'implémentation du moteur d'exécution Ruby. Il suit la parité avec la référence Python lorsque cela est approprié tout en respectant les idiomes Ruby.

## Objectifs

- Exécuter SCXML/SCJSON avec une sémantique compatible SCION
- Sortie de trace JSONL déterministe (schéma correspondant à Python)
- Modes laxiste/strict analogues à Python
- Support du cycle de vie invoke/finalize multi-documents

## Composants

- `Scjson::Engine` – point d'entrée public pour le traçage de l'exécution (`engine.rb`)
- CLI: `scjson engine-trace` – wrapper autour de `Scjson::Engine.trace`
- Futur: runtime de base (contexte de document, activation/configuration, file d'événements)

## Schéma de trace

Chaque ligne de trace est un objet JSON avec les champs suivants:

- `step` – numéro d'étape entier (0 est l'initialisation)
- `event` – `{ "name": string, "data": any } | null`
- `configuration` – `[string]` configuration active actuelle
- `enteredStates` / `exitedStates` – `[string]` deltas pour l'étape
- `firedTransitions` – `[object]` transitions prises à cette étape
- `actionLog` – `[object]` actions exécutées (ordre préservé)
- `datamodelDelta` – `{string: any}` changements du modèle de données (clés normalisées)

## Algorithme d'exécution (aperçu)

1. Initialisation (étape 0): calcul de la configuration initiale
2. Traitement des événements: boucle macrostep jusqu'à la quiescence, microsteps par ensemble de transitions (sélection de transition unique de base implémentée; résolution des conflits en attente)
3. Minuteurs: prend en charge la planification `<send delay>` et les jetons de contrôle `advance_time` dans les flux d'événements pour vider les minuteurs de manière déterministe

## Parité avec Python

- Indicateurs: `--leaf-only`, `--omit-delta`, `--omit-actions`, `--omit-transitions`, `--advance-time`, `--ordering`
- Normalisation: la suppression du bruit de l'étape 0 est gérée dans l'outil de comparaison
- Couverture et vecteurs: réutilisation du générateur et du harnais Python

## État

L'implémentation initiale fournit une CLI fonctionnelle (`engine-trace`) avec:
- Trace de l'étape 0, configuration entrée
- Événements externes + internes, quiescence sans événement
- Ordre de sortie/entrée basé sur LCA (microsteps de transition unique)
- Contenu exécutable: log, assign, raise, if/elseif/else, foreach
- Minuteurs: `<send delay>` avec vidage `advance_time`

Le travail en attente comprend la résolution des conflits et la sémantique complète parallèle/historique pour atteindre un comportement compatible SCION.

Voir aussi
- Guide de l'utilisateur: `docs/ENGINE-RB.md`
- Plan de la liste de contrôle: `docs/TODO-ENGINE-RUBY.md`
