<p align="center"><img src="scjson.png" alt="scjson logo" width="200"/></p>

# AGENTS

Ce fichier définit les agents et leurs rôles respectifs pour le projet `scjson`. Chaque agent est responsable d'une tâche spécifique de transformation, de validation ou d'extraction.

---
## Configuration Python
Python est configuré avec tous les modules spécifiés. N'exécutez pas pip ou poetry.

## Configuration JavaScript
Le fichier package.json du répertoire js spécifie dist/index.js comme point d'entrée. Par conséquent, le paquet doit être compilé avec 'npm run build' avant l'exécution via Node ou les tests après les modifications avec uber_test.py.


## Exigences de documentation et d'attribution

Tous les agents **doivent** inclure :

- Une **chaîne de documentation de niveau module** complète en haut de chaque fichier
- Des chaînes de documentation pour les classes et les fonctions, y compris les paramètres/retours de style doxygen.
- L'attribution au niveau du fichier au format suivant :

```python
"""
Agent Name: <descriptive identifier>

Part of the scjson project.
Developed by Softoboros Technology Inc.
Licensed under the BSD 1-Clause License.
"""
```

### Politique de maintenance des listes de contrôle

- Tous les fichiers `docs/TODO-*.md` sont des listes de contrôle vivantes.
- Tenez-les à jour : les éléments cochés reflètent les fonctionnalités qui ont été intégrées ; les éléments non cochés sont en attente.
- Lors de l'implémentation ou de la modification de fonctionnalités qui affectent une liste de contrôle, mettez à jour le `docs/TODO-*.md` correspondant dans la même modification.

---

## Agent : scxml-to-scjson

- **Entrée** : document SCXML (`*.scxml`, format XML)
- **Sortie** : objet SCJSON (`*.scjson`, format JSON)
- **Mode** : transformation structurelle unidirectionnelle
- **Validation** : par rapport à `scjson.schema.json`
- **Notes** :
  - Convertit la structure des balises, les attributs et l'imbrication du XML au JSON
  - Supprime les commentaires et les extensions SCXML non prises en charge
  - Préserve la hiérarchie et la sémantique d'exécution

---

## Agent : scjson-to-scxml

- **Entrée** : objet SCJSON (`*.scjson`, format JSON)
- **Sortie** : document SCXML (`*.scxml`, format XML)
- **Mode** : transformation réversible
- **Validation** : par rapport au SCXML XSD (`scxml.xsd`)
- **Notes** :
  - Génère un SCXML valide conforme au schéma W3C
  - La sortie est fonctionnellement équivalente à l'entrée, la structure en premier

---

## Agent : validate-scjson

- **Entrée** : objet SCJSON (`*.scjson`)
- **Sortie** : Réussite/Échec + liste des erreurs de validation
- **Mode** : Sans état
- **Validateur** : `scjson.schema.json`
- **Notes** :
  - Peut être utilisé indépendamment ou comme étape préliminaire
  - Compatible avec les bibliothèques de validation `jsonschema`

---

## Agent : validate-scxml

- **Entrée** : document SCXML (`*.scxml`)
- **Sortie** : Réussite/Échec + liste des erreurs de validation
- **Mode** : Sans état
- **Validateur** : `scxml.xsd` (W3C)
- **Notes** :
  - Nécessite un validateur de schéma XML (par exemple, lxml, xmllint)
  - Suppose une entrée XML encodée en UTF-8

---

## Agent : generate-jsonschema

- **Entrée** : définitions de modèle Pydantic internes
- **Sortie** : Schéma JSON (`scjson.schema.json`)
- **Mode** : Au moment de la construction
- **Notes** :
  - Schéma canonique utilisé pour toute validation SCJSON
  - Doit être régénéré si les modèles changent

---

## Agent : roundtrip-test

- **Entrée** : SCXML → SCJSON → SCXML
- **Sortie** : Réussite/Échec + différences
- **Mode** : Utilitaire de test
- **Notes** :
  - Détecte la perte de fidélité ou la dérive sémantique
  - Utile pour l'intégration CI et les vérifications de régression

---

## Agent : schema-dump

- **Entrée** : fichier SCJSON
- **Sortie** : Bloc de métadonnées ou résumé de la structure
- **Mode** : Introspectif
- **Notes** :
  - Affiche la balise racine, le nombre d'états et la couverture des fonctionnalités
  - Facultatif : hachage de la structure pour la correspondance des tests
