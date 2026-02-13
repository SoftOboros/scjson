```markdown
<p align="center"><img src="https://raw.githubusercontent.com/SoftOboros/scjson/main/scjson.png" alt="scjson logo" width="200"/></p>

# scjson Package JavaScript

Ce répertoire contient l'implémentation JavaScript de **scjson**, un format pour représenter les machines d'état SCXML en JSON. Le paquet fournit une interface en ligne de commande pour convertir entre les fichiers `.scxml` et `.scjson` et pour valider les documents par rapport au schéma du projet.

Pour plus de détails sur la manière dont les éléments SCXML sont inférés pendant la conversion, consultez [INFERENCE.md](https://github.com/SoftOboros/scjson/blob/main/INFERENCE.md).

Le paquet inclut les types TypeScript pour les fonctions et les fonctions par défaut pour les renvoyer.

## Installation

```bash
npm install scjson
```

Vous pouvez également l'installer à partir d'une copie de ce dépôt :

```bash
cd js && npm install
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

## Utilisation en ligne de commande

Après l'installation, la commande `scjson` est disponible :

```bash
# Convertir un seul fichier
scjson json path/to/machine.scxml

# Reconvertir en SCXML
scjson xml path/to/machine.scjson

# Valider récursivement
scjson validate path/to/dir -r
```

## CLI de test (SCION)

Le paquet inclut également un CLI de test qui exécute SCXML à l'aide du moteur SCION
et émet des traces JSONL compatibles avec les outils de comparaison.

Installer la dépendance homologue :
```bash
npm i scion-core
```

Utilisation :
```bash
npx scjson-scion-trace -I path/to/chart.(scxml|scjson) -e path/to/events.jsonl [--xml]
```

Vérification rapide (depuis ce dépôt) :
```bash
cd js
npm ci
npm run harness:sample
```

Drapeaux :
- `--leaf-only` – émet des configurations feuille-seulement (SCION rapporte déjà les états atomiques)
- `--omit-delta` – efface `datamodelDelta`
- `--omit-transitions` – efface `firedTransitions`
- `--strip-step0-noise` – à l'étape 0, efface `datamodelDelta` et `firedTransitions`
- `--strip-step0-states` – à l'étape 0, efface `enteredStates` et `exitedStates`

Notes :
- L'entrée `.scjson` est convertie en SCXML en interne avant l'exécution.
- SCION ne modélise pas le temps ; les jetons de contrôle `{"advance_time": N}` émettent une
  étape synthétique pour maintenir la progression des flux.

## Fonctions de conversion
```js
/**
 * xmlToJson
 * Convertit une chaîne SCXML en scjson.
 *
 * @backend/istate/tests/data/SCXML-tutorial/Doc/param.md {string} xmlStr - Entrée XML.
 * @backend/istate/tests/data/SCXML-tutorial/Doc/param.md {boolean} [omitEmpty=true] - Supprime les valeurs vides si vrai.
 * @returns {string} Représentation JSON.
 */

/**
 * jsonToXml
 * Convertit une chaîne scjson en SCXML.
 *
 * @backend/istate/tests/data/SCXML-tutorial/Doc/param.md {string} jsonStr - Entrée JSON.
 * @returns {string} Sortie XML.
 */
```

## Utilisation courante de la traduction JS
```js
const { xmlToJson, jsonToXml } = require('scjson');

```

## Utilisation de la traduction ESR
```js
import { xmlToJson, jsonToXml }from "scjson/browser"
```

## Convertisseurs partagés
Les versions Node et navigateur utilisent la même logique de conversion exposée dans
`scjson/converters`. Vous pouvez importer ces aides directement si vous avez besoin d'accéder à
les fonctions utilitaires utilisées par la CLI et les modules de navigateur.
```js
import { xmlToJson, jsonToXml } from 'scjson/converters';
```

## Exemple de point de terminaison Axios
```typescript
import axios from "axios"
import * as scjson from "scjson/props"

// Une fonction pour créer un nouveau document avec trois états et transitions.
const newScxml = (): scjson.ScxmlProps => {
  const doc: scjson.ScxmlProps = scjson.defaultScxml();
  let state: scjson.StateProps = scjson.defaultState();
  let transition: scjson.TransitionProps = scjson.defaultTransition();
  doc.name = 'New State Machine';
  doc.exmode = scjson.ExmodeDatatypeProps.Lax;
  doc.binding = scjson.BindingDatatypeProps.Early;
  doc.initial.push('Start');
  state.id = 'Start';
  transition.target.push('Process');
  state.transition.push(transition);
  doc.state.push(state);
  state = scjson.defaultState();
  state.id = 'Process';
  transition = scjson.defaultTransition();
  transition.target.push('End');
  state.transition.push(transition);
  doc.state.push(state);
  state = scjson.defaultState();
  state.id = 'End';
  transition = scjson.defaultTransition();
  transition.target.push('Start');
  state.transition.push(transition);
  doc.state.push(state);
  return doc;
}

// Créer une instance Axios
const ax = axios.create({
  baseURL: "https://api.example.com/scxml",
  headers: { "Content-Type": "application/json" },
  withCredentials: true,
});

// Exporter une fonction pour envoyer le document
export const sendNewScxml = () => {
  const doc = newScxml();
  ax.post('/newDoc', doc);
}

```

## Problèmes connus
Aucun pour le moment.

Les tests de conformité opérationnelle sont effectués via [uber_test.py](https://github.com/SoftOboros/scjson/blob/engine/py/uber_test.py)
```bash
/py# python uber_test.py -l javascript 2>&1 | tee test.log
```
Note : [uber_test.py](https://github.com/SoftOboros/scjson/blob/main/py/uber_test.py) applique tous les fichiers scxml du [Tutoriel ScxmlEditor de Zhornyak](https://alexzhornyak.github.io/ScxmlEditor-Tutorial/) qui fournit un ensemble robuste de vecteurs de test scxml utiles pour la vérification de la conformité aux normes. C'est le seul fichier de la suite de tests qui échoue à la vérification aller-retour.


### `scjson/props`

### Énumérations

Chaque énumération représente un ensemble de chaînes restreint utilisé par SCXML. Les valeurs
présentées ci-dessous reflètent celles définies dans le schéma SCJSON.

Les énumérations utilisent ce modèle pour permettre que toutes les parties statiques et dynamiques soient traitées séparément,
mais mappées au même nom.
```typescript
export const BooleanDatatypeProps = {
    False: "false",
    True: "true",
} as const;

export type BooleanDatatypeProps = typeof BooleanDatatypeProps[keyof typeof BooleanDatatypeProps];
```

- `AssignTypeDatatypeProps` – comment l'élément `<assign>` manipule le modèle de données.
  Valeurs : `replacechildren`, `firstchild`, `lastchild`, `previoussibling`,
  `nextsibling`, `replace`, `delete`, `addattribute`.
- `BindingDatatypeProps` – détermine si les variables du modèle de données sont liées `early` ou
  `late` pendant l'exécution.
- `BooleanDatatypeProps` – valeurs d'attribut booléennes `true` ou `false`.
- `ExmodeDatatypeProps` – mode d'exécution du processeur, soit `lax` ou `strict`.
- `HistoryTypeDatatypeProps` – type d'état `<history>` : `shallow` ou `deep`.
- `TransitionTypeDatatypeProps` – si une `<transition>` est `internal` ou
  `external`.

### Types courants

Plusieurs classes générées partagent des champs d'aide génériques :

- `other_attributes` : `Record<str, str>` capturant des attributs XML supplémentaires de
  espaces de noms étrangers.
- `other_element` : `list[object]` permettant de conserver des nœuds enfants non typés d'autres
  espaces de noms.
- `content` : `list[object]` utilisé lorsque les éléments permettent un contenu mixte ou générique.


### Types de documents / objets
Types TypeScript simples sans validation d'exécution.
- `AssignProps` `AssignArray`         – met à jour un emplacement du modèle de données avec une expression ou une valeur.
- `CancelProps` `CancelArray`         – annule une opération `<send>` en attente.
- `ContentProps` `ContentArray`       – charge utile en ligne utilisée par `<send>` et `<invoke>`.
- `DataProps` `DataArray`             – représente une seule variable du modèle de données.
- `DatamodelProps` `DatamodelArray`   – conteneur pour un ou plusieurs éléments `<data>`.
- `DonedataProps` `DonedataArray`     – charge utile renvoyée lorsqu'un état `<final>` est atteint.
- `ElseProps`                         – branche de secours pour les conditions `<if>`.
- `ElseifProps`                       – branche conditionnelle suivant un `<if>`.
- `FinalProps` `FinalArray`           – marque un état terminal dans la machine.
- `FinalizeProps` `FinalizeArray`     – exécuté après la fin d'un `<invoke>`.
- `ForeachProps` `ForeachArray`       – itère sur les éléments au sein du contenu exécutable.
- `HistoryProps` `HistoryArray`       – pseudostate se souvenant des enfants actifs précédents.
- `IfProps` `IfArray`                 – bloc d'exécution conditionnel.
- `InitialProps` `InitialArray`       – état initial au sein d'un état composé.
- `InvokeProps` `InvokeArray`         – exécute un processus ou une machine externe.
- `LogProps` `LogArray`               – instruction de sortie de diagnostic.
- `OnentryProps` `OnentryArray`       – actions effectuées lors de l'entrée dans un état.
- `OnexitProps` `OnexitArray`         – actions effectuées lors de la sortie d'un état.
- `ParallelProps` `ParallelArray`     – coordonne les régions concurrentes.
- `ParamProps` `ParamArray`           – paramètre passé à `<invoke>` ou `<send>`.
- `RaiseProps` `RaiseArray`           – déclenche un événement interne.
- `ScriptProps` `ScriptArray`         – script exécutable en ligne.
- `ScxmlProps`                        – élément racine d'un document SCJSON.
- `SendProps` `SendArray`             – distribue un événement externe.
- `StateProps` `StateArray`           – nœud d'état de base.
- `TransitionProps` `TransitionArray` – arête entre les états déclenchée par des événements.

### Gestion des objets
- Kind - marqueur unique pour chacun des types.
```typescript
export type Kind = "number" | "string" | "record<string, object>" | "number[]" | "string[]"
                   | "record<string, object>[]" | "assign" | "assigntypedatatype" | "bindingdatatype" | "booleandatatype"
                   | "cancel" | "content" | "data" | "datamodel" | "donedata" | "else" | "elseif"
                   | "exmodedatatype" | "final" | "finalize" | "foreach" | "history" | "historytypedatatype" | "if"
                   | "initial" | "invoke" | "log" | "onentry" | "onexit" | "parallel" | "param" | "raise"
                   | "script" | "scxml" | "send" | "state" | "transition" | "transitiontypedatatype"
                   | "assignarray" | "cancelarray" | "contentarray" | "dataarray" | "datamodelarray"
                   | "donedataarray" | "finalarray" | "finalizearray" | "foreacharray" | "historyarray" | "ifarray"
                   | "initialarray" | "invokearray" | "logarray" | "onentryarray" | "onexitarray" | "parallelarray"
                   | "paramarray" | "raisearray" | "scriptarray" | "sendarray" | "statearray" | "transitionarray";
```
- PropsUnion - une union des types utilisés dans le modèle de données scxml
```typescript
export type PropsUnion = null | string | number | Record<string, object> | string[] | number[]
                         | Record<string, object>[] | AssignProps | AssignTypeDatatypeProps | BindingDatatypeProps
                         | BooleanDatatypeProps | CancelProps | ContentProps | DataProps | DatamodelProps | DonedataProps
                         | ElseProps | ElseifProps | ExmodeDatatypeProps | FinalProps | FinalizeProps | ForeachProps
                         | HistoryProps | HistoryTypeDatatypeProps | IfProps | InitialProps | InvokeProps | LogProps
                         | OnentryProps | OnentryArray | OnexitProps | OnexitArray | ParallelProps | ParamProps
                         | RaiseProps | ScriptProps | ScxmlProps | SendProps | StateProps | TransitionProps | TransitionTypeDatatypeProps
                         | AssignArray | CancelArray | ContentArray | DataArray | DatamodelArray | DonedataArray
                         | FinalArray | FinalizeArray | ForeachArray | HistoryArray | IfArray | InitialArray
                         | InvokeArray | LogArray | OnentryArray | OnexitArray | ParallelArray | ParamArray
                         | RaiseArray | ScriptArray | ScxmlProps | SendArray | StateArray | TransitionArray;
```
- KindMap - mappe le nom de la chaîne au type pour les objets utilisés dans le modèle de données scxml
```typescript
export type KindMap = {
    assign: AssignProps
    assignarray: AssignArray
    assigntypedatatype: AssignTypeDatatypeProps
    bindingdatatype: BindingDatatypeProps
    booleandatatype: BooleanDatatypeProps
    cancel: CancelProps
    cancelarray: CancelArray
    content: ContentProps
    contentarray: ContentArray
    data: DataProps
    dataarray: DataArray
    datamodel: DatamodelProps
    datamodelarray: DatamodelArray
    donedata: DonedataProps
    donedataarray: DonedataArray
    else: ElseProps
    elseif: ElseifProps
    exmodedatatype: ExmodeDatatypeProps
    final: FinalProps
    finalarray: FinalArray
    finalize: FinalizeProps
    finalizearray: FinalizeArray
    foreach: ForeachProps
    foreacharray: ForeachArray
    history: HistoryProps
    historyarray: HistoryArray
    historytypedatatype: HistoryTypeDatatypeProps
    if: IfProps
    ifarray: IfArray
    initial: InitialProps
    initialarray: InitialArray
    invoke: InvokeProps
    invokearray: InvokeArray
    log: LogProps
    logarray: LogArray
    onentry: OnentryProps
    onentryarray: OnentryArray
    onexit: OnexitProps
    onexitarray: OnexitArray
    parallel: ParallelProps
    parallelarray: ParallelArray
    param: ParamProps
    paramarray: ParamArray
    raise: RaiseProps
    raisearray: RaiseArray
    script: ScriptProps
    scriptarray: ScriptArray
    scxml: ScxmlProps
    send: SendProps
    sendarray: SendArray
    state: StateProps
    statearray: StateArray
    transition: TransitionProps
    transitionarray: TransitionArray
    transitiontypedatatype: TransitionTypeDatatypeProps
}
```


### Autres ressources
GitHub : [https://github.com/SoftOboros/scjson]
```bash
git clone https://github.com/SoftOboros/scjson.git

git clone git @github.com:SoftOboros/scjson.git

gh repo clone SoftOboros/scjson
```

PyPI : [https://pypi.org/project/scjson/]
```bash
pip install scjson
```

Cargo : [https://crates.io/crates/scjson]
```bash
cargo install scjson
```

DockerHub : [https://hub.docker.com/r/iraa/scjson]
(Environnement de développement complet pour toutes les langues prises en charge)
```bash
docker pull iraa/scjson:latest
```


Tout le code source de ce répertoire est publié sous la licence BSD 1-Clause. Voir [LICENSE](./LICENSE) et [LEGAL.md](./LEGAL.md) pour plus de détails.
```
