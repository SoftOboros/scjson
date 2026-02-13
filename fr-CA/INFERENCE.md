```markdown
<p align="center"><img src="scjson.png" alt="scjson logo" width="200"/></p>

# Guide d'inférence SCXML vers SCJSON

Ce document décrit comment le convertisseur JavaScript transforme le SCXML au format `scjson`. Il capture la *logique d'inférence* encodée dans [`js/src/converters.js`](js/src/converters.js) afin que d'autres implémentations linguistiques puissent reproduire un comportement identique.

## 1. Aperçu

- **SCJSON** est une représentation JSON structurée du SCXML.
- Le convertisseur fait plus que copier les noms d'éléments. Certaines structures SCXML sont **inférées** et attachées directement à leurs objets parents.
- Comprendre ces règles permet aux développeurs d'implémenter des convertisseurs compatibles en Rust, Python ou toute autre langue.

## 2. Point d'entrée de la conversion

- L'élément racine est `<scxml>`.
- Chaque élément devient un objet avec un champ `"tag"` contenant le nom de la balise.
- Tous les attributs XML sont copiés en tant que propriétés de chaîne au même niveau que `tag`.
- Les enfants sont traités de manière récursive.

## 3. Extraction de champs structurels

Le convertisseur extrait des éléments enfants spécifiques de `content[]` afin qu'ils résident directement sur l'objet parent. Chacune des balises suivantes devient une propriété de tableau sur son parent :

- `state`
- `parallel`
- `final`
- `history`
- `transition`
- `onentry`
- `onexit`
- `invoke`
- `datamodel`
- `data`
- `initial`
- `script`
- `log`
- `assign`
- `send`
- `cancel`

Lorsque l'un de ces éléments est présent :

1. Initialisez un tableau pour la propriété correspondante (par exemple, `state: []`).
2. Placez les objets enfants convertis dans ce tableau.
3. Ne laissez pas l'élément brut dans `content[]` à moins que sa balise ne soit inconnue.

## 4. Gestion du tableau de contenu

- Les enfants qui ne correspondent pas à un champ structurel restent dans `content[]`.
- L'ordre est préservé, et chaque enfant est converti de manière récursive.
- Les attributs sont aplatis sur chaque objet.
- Une balise vide devient `{ "tag": "..." }` sans champs supplémentaires.

## 5. Autres attributs et solutions de repli

- Tous les attributs XML sont conservés exactement sous forme de chaînes.
- L'utilisation d'espaces de noms n'est pas appliquée sauf si elle est explicitement ajoutée par de futures versions.
- Les éléments et attributs inconnus sont conservés sans générer d'erreurs.
- Ces points sont des crochets d'extension pour de futures mises à jour de schémas.

## 6. Exemples

### Entrée SCXML
```xml
<state id="parent">
  <transition event="go" target="child"/>
  <state id="child"/>
  <onentry>
    <log label="start" expr="enter"/>
    <foo/>
  </onentry>
</state>
```

### SCJSON converti
```json
{
  "tag": "state",
  "id": "parent",
  "transition": [{
    "tag": "transition",
    "event": "go",
    "target": ["child"]
  }],
  "state": [{ "tag": "state", "id": "child" }],
  "onentry": [{
    "tag": "onentry",
    "log": [{ "tag": "log", "label": "start", "expr": "enter" }],
    "content": [{ "tag": "foo" }]
  }]
}
```

L'élément inconnu `<foo/>` reste dans `content[]` du bloc `onentry`.

## 7. Notes sur le déterminisme

- Les conversions sont déterministes : le même SCXML produit un SCJSON identique.
- Les espaces blancs n'ont aucun effet structurel.
- L'ordre des attributs n'influence pas la sortie.

## 8. Conseils d'implémentation

- Une approche de descente récursive est utilisée.
- Utilisez `element.tagName`, `element.attributes` et `element.children` lors du parcours du DOM.
- `STRUCTURAL_FIELDS` est un `Set` contrôlant si un enfant est extrait de `content[]`.
```
