```markdown
<p align="center"><img src="https://raw.githubusercontent.com/SoftOboros/scjson/main/scjson.png" alt="scjson logo" width="200"/></p>

# Paquetage Python scjson

Ce répertoire contient l'implémentation Python de **scjson**, un format pour représenter les machines d'état SCXML en JSON. Le paquetage fournit une interface de ligne de commande et des fonctions utilitaires pour convertir entre les fichiers `.scxml` et `.scjson` et pour valider les documents par rapport au schéma du projet.

Le paquetage comprend des types pydantic et dataclasses pour les objets/énumérations associés, sous formes standard et strictes.

Pour plus de détails sur la manière dont les éléments SCXML sont inférés pendant la conversion, voir [INFERENCE.md](https://github.com/SoftOboros/scjson/blob/main/INFERENCE.md). En Python, l'inférence pour la conversion est gérée par les modèles de dataclasses. Voir ci-dessous.

## Installation

```bash
pip install scjson
```

Vous pouvez également l'installer à partir d'un extrait de ce dépôt :

```bash
cd py && pip install -e .
```

## Code Source - Support Multi-Langues
[https://github.com/SoftOboros/scjson/]
- csharp
- go
- java
- javascript / typescript
- lua
- python
- ruby
- rust
- swift

## Moteur Python — Guide d'Utilisation

Pour une utilisation de bout en bout du moteur d'exécution Python (traçage, comparaison à une référence, génération de vecteurs, balayage de corpus), voir :

- docs/ENGINE-PY.md (dans ce dépôt)

En ligne : https://github.com/SoftOboros/scjson/blob/main/docs/ENGINE-PY.md

## Dépendance de Référence SCION

Plusieurs tests de comparaison (`py/tests/test_exec_compare_advanced.py`) et les outils `exec_compare` invoquent le lanceur [SCION](https://www.npmjs.com/package/scion) basé sur Node, regroupé sous `tools/scion-runner`. Node.js doit être capable de résoudre les paquetages [SCION](https://www.npmjs.com/package/scion) (`scxml`, `jsdom` et `regenerator-runtime`) via son chargeur de modules. Installez-les une fois avant d'exécuter les comparaisons :

```bash
cd tools/scion-runner
npm ci  # ou npm install
```

Lors de l'exécution des tests Python ou des comparaisons CLI, assurez-vous que `node` peut charger ces modules (par exemple en conservant l'installation ci-dessus en place ou en ajoutant leur emplacement à `NODE_PATH`). Sans les paquetages [SCION](https://www.npmjs.com/package/scion), les comparaisons reviennent au moteur Python.

## Utilisation en Ligne de Commande

Après l'installation, la commande `scjson` est disponible :

```bash
# Convertir un seul fichier
scjson json path/to/machine.scxml

# Convertir de nouveau en SCXML
scjson xml path/to/machine.scjson - o path/to/output.scxml

# Valider de manière récursive
scjson validate path/to/dir -r

# Générer des Types TypeScript
scjson  typescript -o dir/of/output

# Générer scjson.schema.json
scjson  schema -o dir/of/output
```

## Exemple d'Utilisation de FastAPI
Ceci est un point de terminaison FastAPI minimal comme exemple d'utilisation de la classe SCXMLDocumentHandler.

```python
import json
from fastapi import FastAPI, Request, HTTPException, Response
from scjson.SCXMLDocumentHandler import SCXMLDocumentHandler

app = FastAPI()
handler = SCXMLDocumentHandler(schema_path=None)

# Stockage en mémoire pour la démo
store = {}

 @app.get("/xml/{slug}")
async def get_xml(slug: str):
    """Return the SCXML document as XML."""
    data = store.get(slug)
    if not data:
        raise HTTPException(status_code=404, detail="Document not found")
    xml_str = handler.json_to_xml(json.dumps(data))
    return Response(content=xml_str, media_type="application/xml")

 @app.post("/xml/{slug}")
async def post_xml(slug: str, request: Request):
    """Accept an SCXML document and convert it to scjson."""
    xml_bytes = await request.body()
    xml_str = xml_bytes.decode("utf-8")
    json_str = handler.xml_to_json(xml_str)
    data = json.loads(json_str)
    data.setdefault("name", slug)
    store[slug] = data
    return data
```

## Importation d'Objets
Ceci importe les définitions de types individuels. Voir ci-dessous pour les variantes de bibliothèque.
Des variantes de classe sont disponibles pour pydantic et les dataclasses implémentant les variantes xsd standard et strictes.

```python
from scjson.pydantic import Scxml, State, Transition, Onentry # etc.

```

## Mises en Garde SCJSON

Les aides à la conversion SCXML normalisent les données afin qu'elles puissent être stockées au format JSON.
Lors de la sérialisation `asdict()`, les dataclasses générées peuvent contenir
des valeurs `Decimal` et des instances d'énumération (par exemple `AssignTypeDatatype`).

- Les valeurs `Decimal` sont converties en nombres à virgule flottante.
- Les valeurs d'énumération sont stockées en utilisant leur chaîne `.value`.

Ces conversions permettent à la représentation JSON d'être sérialisée par
`json.dumps` puis reconvertie via l'aide `_to_dataclass`.

## Problèmes Connus
Aucun pour le moment.

Le test de conformité opérationnelle est effectué via [uber_test.py](https://github.com/SoftOboros/scjson/blob/engine/py/uber_test.py)
```bash
/py# python uber_test.py -l python 2>&1 | tee test.log
```
Note : [uber_test.py](https://github.com/SoftOboros/scjson/blob/main/py/uber_test.py) applique tous les fichiers scxml du [Tutoriel ScxmlEditor de Zhornyak](https://alexzhornyak.github.io/ScxmlEditor-Tutorial/) qui fournit un ensemble robuste de vecteurs de test scxml utiles pour la vérification de la conformité standard. C'est le seul fichier de la suite de tests qui échoue à vérifier l'aller-retour.

### Harnais de Test Uber

Exécuter sur toutes les langues ou une seule langue avec support d'alias :

```bash
# Toutes les langues détectées sur PATH
python py/uber_test.py

# Langue unique (alias autorisés) : py, python, js, ts, javascript, rs, rust, swift, java, csharp
python py/uber_test.py -l js
python py/uber_test.py -l swift   # faute de frappe tolérée → swift

# Limiter le corpus et traiter le consensus uniquement comme des avertissements
python py/uber_test.py -l swift -s "Examples/Qt/StopWatch/*.scxml" --consensus-warn
```

- `-s/--subset` filtre les fichiers SCXML par un glob relatif à `tutorial/`.
- `--consensus-warn` dégrade les incohérences en avertissements lorsque les langues de référence (Python/JavaScript/Rust) correspondent à la structure canonique.
- Le harnais normalise les différences structurelles (voir INFERENCE.md) pour produire des diffs exploitables et imprime une ligne de triage avec une recommandation.

## Variantes de Modèles

Le paquetage Python expose quatre ensembles de modèles générés qui reflètent le
schéma SCJSON. Ils partagent tous les mêmes noms de champs et énumérations, mais
offrent des caractéristiques d'exécution différentes.

### Énumérations

Chaque énumération représente un ensemble de chaînes restreint utilisé par SCXML. Les valeurs
présentées ci-dessous reflètent celles définies dans le schéma SCJSON.

- `AssignTypeDatatype` – comment l'élément `<assign>` manipule le modèle de données.
  Valeurs : `replacechildren`, `firstchild`, `lastchild`, `previoussibling`,
  `nextsibling`, `replace`, `delete`, `addattribute`.
- `BindingDatatype` – détermine si les variables du modèle de données sont liées `early` ou
  `late` pendant l'exécution.
- `BooleanDatatype` – valeurs d'attribut booléennes `true` ou `false`.
- `ExmodeDatatype` – mode d'exécution du processeur, `lax` ou `strict`.
- `HistoryTypeDatatype` – type d'état `<history>` : `shallow` ou `deep`.
- `TransitionTypeDatatype` – si une `<transition>` est `internal` ou
  `external`.

## Types Communs

Plusieurs classes générées partagent des champs d'aide génériques :

- `other_attributes` : `dict[str, str]` capturant des attributs XML supplémentaires de
  espaces de noms étrangers.
- `other_element` : `list[object]` permettant la préservation de nœuds enfants non typés d'autres
  espaces de noms.
- `content` : `list[object]` utilisé lorsque les éléments autorisent un contenu mixte ou générique.

### `scjson.dataclasses`

Dataclasses Python simples sans validation à l'exécution.

- `Assign` – met à jour un emplacement du modèle de données avec une expression ou une valeur.
- `Cancel` – annule une opération `<send>` en attente.
- `Content` – charge utile en ligne utilisée par `<send>` et `<invoke>`.
- `Data` – représente une seule variable du modèle de données.
- `Datamodel` – conteneur pour un ou plusieurs éléments `<data>`.
- `Donedata` – charge utile renvoyée lorsqu'un état `<final>` est atteint.
- `Else` – branche de repli pour les conditions `<if>`.
- `Elseif` – branche conditionnelle suivant un `<if>`.
- `Final` – marque un état terminal dans la machine.
- `Finalize` – exécuté après la complétion d'un `<invoke>`.
- `Foreach` – itère sur les éléments dans le contenu exécutable.
- `History` – pseudo-état mémorisant les enfants actifs précédents.
- `If` – bloc d'exécution conditionnel.
- `Initial` – état initial dans un état composé.
- `Invoke` – exécute un processus ou une machine externe.
- `Log` – instruction de sortie diagnostique.
- `Onentry` – actions effectuées lors de l'entrée dans un état.
- `Onexit` – actions effectuées lors de la sortie d'un état.
- `Parallel` – coordonne des régions concurrentes.
- `Param` – paramètre passé à `<invoke>` ou `<send>`.
- `Raise` – déclenche un événement interne.
- `Script` – script exécutable en ligne.
- `Scxml` – élément racine d'un document SCJSON.
- `Send` – expédie un événement externe.
- `State` – nœud d'état de base.
- `Transition` – arête entre les états déclenchée par des événements.

### `scjson.dataclasses_strict`

Les mêmes dataclasses que ci-dessus, mais configurées pour une vérification de type plus stricte.

### `scjson.pydantic`

Classes `BaseModel` Pydantic générées à partir du schéma SCJSON. Elles fournissent
une validation des données et des aides `.model_dump()` pratiques.

### `scjson.pydantic_strict`

Modèles Pydantic avec des paramètres de validation stricts.

### Autres Ressources
github: [https://github.com/SoftOboros/scjson]
```bash
git clone https://github.com/SoftOboros/scjson.git

git clone git @github.com:SoftOboros/scjson.git

gh repo clone SoftOboros/scjson
```

npm: [https://www.npmjs.com/package/scjson]
```bash
npm install scjson
```

cargo: [https://crates.io/crates/scjson]
```bash
cargo install scjson
```

dockerhub: [https://hub.docker.com/r/iraa/scjson]
(Environnement de développement complet pour toutes les langues supportées)
```bash
docker pull iraa/scjson:latest
```

## Licence

Tout le code source de ce répertoire est publié sous la Licence BSD 1-Clause. Voir [LICENSE](./LICENSE) et [LEGAL.md](./LEGAL.md) pour plus de détails.
```
